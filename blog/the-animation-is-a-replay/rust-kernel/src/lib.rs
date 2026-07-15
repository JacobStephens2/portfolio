//! A hand-rolled DES kernel and the factory model, compiled to WebAssembly.
//! No simulation dependencies: the kernel is a BinaryHeap keyed on
//! (time, sequence) and a seeded PCG32. The point of this crate is the post's
//! Fig. 3 claim: the kernel is an afternoon; the ecosystem is the hard part.

use std::cmp::Ordering;
use std::collections::BinaryHeap;
use wasm_bindgen::prelude::*;

// ---- The kernel (shown in the post, Fig. 3) ----

struct Scheduled<E> {
    t: f64,
    seq: u64,
    event: E,
}

impl<E> PartialEq for Scheduled<E> {
    fn eq(&self, other: &Self) -> bool {
        self.t == other.t && self.seq == other.seq
    }
}
impl<E> Eq for Scheduled<E> {}
impl<E> Ord for Scheduled<E> {
    fn cmp(&self, other: &Self) -> Ordering {
        // Reversed: BinaryHeap is a max-heap, we want the earliest event first.
        other
            .t
            .total_cmp(&self.t)
            .then_with(|| other.seq.cmp(&self.seq))
    }
}
impl<E> PartialOrd for Scheduled<E> {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

struct Kernel<E> {
    heap: BinaryHeap<Scheduled<E>>,
    seq: u64,
}

impl<E> Kernel<E> {
    fn new() -> Self {
        Kernel { heap: BinaryHeap::new(), seq: 0 }
    }
    fn schedule(&mut self, t: f64, event: E) {
        self.heap.push(Scheduled { t, seq: self.seq, event });
        self.seq += 1;
    }
    fn next(&mut self) -> Option<(f64, E)> {
        self.heap.pop().map(|s| (s.t, s.event))
    }
}

// ---- Seeded RNG: PCG32 (Melissa O'Neill's PCG-XSH-RR) ----

struct Pcg32 {
    state: u64,
    inc: u64,
}

impl Pcg32 {
    fn new(seed: u64) -> Self {
        let mut rng = Pcg32 { state: 0, inc: (54u64 << 1) | 1 };
        rng.state = rng.state.wrapping_add(seed);
        rng.next_u32();
        rng
    }
    fn next_u32(&mut self) -> u32 {
        let old = self.state;
        self.state = old
            .wrapping_mul(6364136223846793005)
            .wrapping_add(self.inc);
        let xorshifted = (((old >> 18) ^ old) >> 27) as u32;
        let rot = (old >> 59) as u32;
        xorshifted.rotate_right(rot)
    }
    /// Uniform in [0, 1).
    fn next_f64(&mut self) -> f64 {
        (self.next_u32() as f64) / 4294967296.0
    }
    fn expo(&mut self, mean: f64) -> f64 {
        -mean * (1.0 - self.next_f64()).ln()
    }
}

// ---- The factory model ----

#[derive(Clone, Copy)]
enum Ev {
    Arrival,
    CodeDone(u32),
    CiDone(u32),
    ReviewDone(u32),
}

pub struct Params {
    pub arrival_mean: f64,
    pub code_mean: f64,
    pub ci_time: f64,
    pub fail_p: f64,
    pub agents: u32,
    pub reviewers: u32,
    pub review_mean: f64,
    pub horizon_min: f64,
}

fn push_event(out: &mut String, t: f64, kind: &str, id: u32) {
    if !out.is_empty() {
        out.push(',');
    }
    out.push_str(&format!("{{\"id\":{},\"t\":{:.6},\"type\":\"{}\"}}", id, t, kind));
}

pub fn run_factory(p: &Params, seed: u64) -> String {
    let mut k: Kernel<Ev> = Kernel::new();
    let mut rng = Pcg32::new(seed);
    let mut events = String::new();

    let mut code_queue: std::collections::VecDeque<u32> = Default::default();
    let mut review_queue: std::collections::VecDeque<u32> = Default::default();
    let (mut agents_busy, mut reviewers_busy, mut next_id) = (0u32, 0u32, 1u32);

    macro_rules! try_code {
        ($t:expr) => {
            while agents_busy < p.agents {
                match code_queue.pop_front() {
                    Some(id) => {
                        agents_busy += 1;
                        push_event(&mut events, $t, "code_start", id);
                        let dt = rng.expo(p.code_mean);
                        k.schedule($t + dt, Ev::CodeDone(id));
                    }
                    None => break,
                }
            }
        };
    }
    macro_rules! try_review {
        ($t:expr) => {
            while reviewers_busy < p.reviewers {
                match review_queue.pop_front() {
                    Some(id) => {
                        reviewers_busy += 1;
                        push_event(&mut events, $t, "review_start", id);
                        let dt = rng.expo(p.review_mean);
                        k.schedule($t + dt, Ev::ReviewDone(id));
                    }
                    None => break,
                }
            }
        };
    }

    let first = rng.expo(p.arrival_mean);
    k.schedule(first, Ev::Arrival);

    while let Some((t, ev)) = k.next() {
        if t > p.horizon_min {
            break;
        }
        match ev {
            Ev::Arrival => {
                let id = next_id;
                next_id += 1;
                push_event(&mut events, t, "arrive", id);
                code_queue.push_back(id);
                let dt = rng.expo(p.arrival_mean);
                k.schedule(t + dt, Ev::Arrival);
                try_code!(t);
            }
            Ev::CodeDone(id) => {
                agents_busy -= 1;
                push_event(&mut events, t, "ci_start", id);
                k.schedule(t + p.ci_time, Ev::CiDone(id));
                try_code!(t);
            }
            Ev::CiDone(id) => {
                if rng.next_f64() < p.fail_p {
                    push_event(&mut events, t, "ci_fail", id);
                    code_queue.push_back(id);
                    try_code!(t);
                } else {
                    push_event(&mut events, t, "ci_pass", id);
                    review_queue.push_back(id);
                    try_review!(t);
                }
            }
            Ev::ReviewDone(id) => {
                reviewers_busy -= 1;
                push_event(&mut events, t, "deploy", id);
                try_review!(t);
            }
        }
    }

    format!(
        "{{\"events\":[{}],\"header\":{{\"engine\":\"rust-wasm-0.1.0\",\"params\":{{\"agents\":{},\"arrivalMean\":{},\"ciTime\":{},\"codeMean\":{},\"failP\":{},\"horizonMin\":{},\"reviewMean\":{},\"reviewers\":{}}},\"schema\":1,\"seed\":{}}}}}",
        events,
        p.agents, p.arrival_mean, p.ci_time, p.code_mean, p.fail_p,
        p.horizon_min, p.review_mean, p.reviewers, seed
    )
}

/// Browser/Node entry point. Returns the event log as canonical JSON.
#[wasm_bindgen]
pub fn run_factory_json(
    seed: u32,
    arrival_mean: f64,
    code_mean: f64,
    ci_time: f64,
    fail_p: f64,
    agents: u32,
    reviewers: u32,
    review_mean: f64,
    horizon_min: f64,
) -> String {
    let p = Params {
        arrival_mean, code_mean, ci_time, fail_p,
        agents, reviewers, review_mean, horizon_min,
    };
    run_factory(&p, seed as u64)
}

/// Fig. 3 toy: five scheduled events, two at the same instant, popped in
/// (time, sequence) order - the ordering rule made visible.
#[wasm_bindgen]
pub fn run_toy() -> String {
    let mut k: Kernel<&str> = Kernel::new();
    k.schedule(3.0, "c");
    k.schedule(1.0, "a");
    k.schedule(2.0, "b1 (scheduled first)");
    k.schedule(2.0, "b2 (scheduled second)");
    k.schedule(0.5, "start");
    let mut out: Vec<String> = Vec::new();
    while let Some((t, e)) = k.next() {
        out.push(format!("{{\"t\":{:.1},\"event\":\"{}\"}}", t, e));
    }
    format!("[{}]", out.join(","))
}
