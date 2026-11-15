#import <Cocoa/Cocoa.h>
#include <errno.h>
#include <fcntl.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/file.h>
#include <unistd.h>

static void refuse(const char *message) {
    fprintf(stderr, "%s\n", message);
    exit(70);
}

static BOOL publish(NSString *root, NSString *name, NSDictionary *value) {
    NSData *data = [NSJSONSerialization dataWithJSONObject:value options:NSJSONWritingSortedKeys error:NULL];
    if (data == nil) {
        refuse("unable to encode an AppKit witness record");
    }
    NSString *path = [root stringByAppendingPathComponent:name];
    NSString *staged = [root stringByAppendingPathComponent:NSUUID.UUID.UUIDString];
    int fd = open(staged.fileSystemRepresentation, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW, 0600);
    if (fd < 0) {
        refuse("unable to stage an AppKit witness record");
    }
    const unsigned char *bytes = data.bytes;
    for (NSUInteger position = 0; position < data.length;) {
        ssize_t count = write(fd, bytes + position, data.length - position);
        if (count < 0 && errno == EINTR) {
            continue;
        }
        if (count <= 0) {
            refuse("unable to write an AppKit witness record");
        }
        position += (NSUInteger)count;
    }
    if (fsync(fd) != 0 || close(fd) != 0) {
        refuse("unable to persist an AppKit witness record");
    }
    if (renameatx_np(AT_FDCWD, staged.fileSystemRepresentation, AT_FDCWD,
                     path.fileSystemRepresentation, RENAME_EXCL) != 0) {
        int reason = errno;
        unlink(staged.fileSystemRepresentation);
        if (reason == EEXIST) {
            return NO;
        }
        refuse("unable to publish an AppKit witness record");
    }
    int directory = open(root.fileSystemRepresentation, O_RDONLY | O_DIRECTORY | O_NOFOLLOW);
    if (directory < 0 || fsync(directory) != 0 || close(directory) != 0) {
        refuse("unable to persist the AppKit witness directory");
    }
    return YES;
}

static BOOL dispatchHeld(NSString *root) {
    NSString *path = [root stringByAppendingPathComponent:@"dispatch.lock"];
    int fd = open(path.fileSystemRepresentation, O_RDWR | O_NOFOLLOW);
    if (fd < 0) {
        return NO;
    }
    int result = flock(fd, LOCK_EX | LOCK_NB);
    int reason = errno;
    close(fd);
    return result == -1 && reason == EWOULDBLOCK;
}

@interface QuitFixture : NSObject <NSApplicationDelegate>
@property(copy) NSString *root;
@property(copy) NSString *attempt;
@property BOOL acceptQuit;
@property BOOL suppressReply;
@property BOOL sawRequest;
@property BOOL sawReplay;
@property NSTimeInterval deadline;
@end

@implementation QuitFixture

- (NSDictionary *)evidence:(NSString *)status {
    if (!pthread_main_np() || NSApp == nil) {
        refuse("quit witness must run on its AppKit main thread");
    }
    return @{@"attempt_id": self.attempt, @"pid": @(getpid()), @"main_thread": @YES,
             @"status": status, @"at": @(NSDate.date.timeIntervalSince1970)};
}

- (void)applicationDidFinishLaunching:(NSNotification *)notification {
    if (notification.object != NSApp ||
        !publish(self.root, @"Ready.json", [self evidence:@"ready"])) {
        refuse("disposable AppKit startup does not identify this application");
    }
}

- (BOOL)applicationShouldOpenUntitledFile:(NSApplication *)sender {
    return NO;
}

- (NSApplicationTerminateReply)applicationShouldTerminate:(NSApplication *)sender {
    if (sender != NSApp || !publish(self.root, @"Delegate.json",
                                    [self evidence:self.acceptQuit ? @"accept" : @"cancel"])) {
        refuse("normal quit delegate was invoked more than once");
    }
    return self.acceptQuit ? NSTerminateNow : NSTerminateCancel;
}

- (void)applicationWillTerminate:(NSNotification *)notification {
    if (notification.object != NSApp || !self.acceptQuit ||
        !publish(self.root, @"WillTerminate.json", [self evidence:@"will_terminate"])) {
        refuse("normal quit notification differs from the accepted delegate");
    }
}

- (void)submit:(NSString *)name {
    NSString *path = [self.root stringByAppendingPathComponent:name];
    NSData *bytes = [NSData dataWithContentsOfFile:path];
    if (bytes.length == 0 || bytes.length > 4096) {
        refuse("invalid disposable request size");
    }
    id request = [NSJSONSerialization JSONObjectWithData:bytes options:0 error:NULL];
    if (![request isKindOfClass:NSDictionary.class] ||
        ![request[@"attempt_id"] isEqual:self.attempt] ||
        ![request[@"pid"] isEqual:@(getpid())] || !dispatchHeld(self.root) ||
        NSDocumentController.sharedDocumentController.documents.count != 0) {
        refuse("disposable normal quit request lost owner or empty-document custody");
    }
    if (!publish(self.root, @"Attempt.json", [self evidence:@"authorization_consumed"])) {
        if (!publish(self.root, @"Duplicate.json", [self evidence:@"duplicate_refused"])) {
            refuse("disposable duplicate receipt was already present");
        }
        return;
    }
    if (!dispatchHeld(self.root) || NSDocumentController.sharedDocumentController.documents.count != 0) {
        refuse("disposable quit authorization lost custody after sealing");
    }
    [NSApp terminate:nil];
    if (!self.suppressReply &&
        !publish(self.root, @"Return.json", [self evidence:@"quit_call_returned"])) {
        refuse("normal quit return receipt was already present");
    }
}

- (void)tick {
    NSFileManager *files = NSFileManager.defaultManager;
    if ([files fileExistsAtPath:[self.root stringByAppendingPathComponent:@"FixtureStop"]]) {
        exit(0);
    }
    if ([NSProcessInfo processInfo].systemUptime >= self.deadline) {
        refuse("disposable AppKit witness exceeded its deadline");
    }
    if (!self.sawRequest && [files fileExistsAtPath:[self.root stringByAppendingPathComponent:@"Request.json"]]) {
        self.sawRequest = YES;
        [self submit:@"Request.json"];
    }
    if (!self.sawReplay && [files fileExistsAtPath:[self.root stringByAppendingPathComponent:@"Replay.json"]]) {
        self.sawReplay = YES;
        [self submit:@"Replay.json"];
    }
}

@end

int main(int argc, const char **argv) {
    @autoreleasepool {
        if (argc != 4) {
            refuse("disposable AppKit witness requires a private directory and case");
        }
        NSString *mode = [NSString stringWithUTF8String:argv[2]];
        BOOL accept = [mode isEqualToString:@"accept"];
        BOOL cancel = [mode isEqualToString:@"cancel"];
        BOOL lost = [mode isEqualToString:@"cancel-reply-loss"];
        if (!accept && !cancel && !lost) {
            refuse("unknown disposable AppKit quit case");
        }
        QuitFixture *delegate = [[QuitFixture alloc] init];
        delegate.root = [NSString stringWithUTF8String:argv[1]];
        delegate.attempt = [NSString stringWithUTF8String:argv[3]];
        delegate.acceptQuit = accept;
        delegate.suppressReply = lost;
        delegate.deadline = [NSProcessInfo processInfo].systemUptime + 30;
        NSApplication *application = NSApplication.sharedApplication;
        application.delegate = delegate;
        [application setActivationPolicy:NSApplicationActivationPolicyAccessory];
        [NSTimer scheduledTimerWithTimeInterval:0.025 repeats:YES block:^(NSTimer *timer) {
            [delegate tick];
        }];
        [application run];
    }
    return 0;
}
