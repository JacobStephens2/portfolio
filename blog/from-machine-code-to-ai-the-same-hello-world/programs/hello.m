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
