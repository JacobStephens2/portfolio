/* Objective-C (Brad Cox / Stepstone 1984; NeXT/Apple lineage).
 * Compiled here with GCC's GNU Objective-C runtime (no Cocoa/GNUstep Foundation).
 * Shows message-send syntax for the same Hello World job as C.
 */
#import <stdio.h>
#import <objc/runtime.h>
#include <stdlib.h>

@interface Greeter {
  Class isa;
}
+ (id)alloc;
- (void)sayHello;
@end

@implementation Greeter
+ (id)alloc {
  return class_createInstance(self, 0);
}
- (void)sayHello {
  puts("Hello, World!");
}
@end

int main(void) {
  Greeter *g = [Greeter alloc];
  [g sayHello];
  object_dispose(g);
  return 0;
}
