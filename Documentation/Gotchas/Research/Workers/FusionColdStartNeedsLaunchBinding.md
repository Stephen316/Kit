# A cold-launch callback can refer to a running instance

AppKit's normal launch options allow an already running instance to receive
the request. Checking for a counterpart just before launch narrows the gap
but does not establish which request created a process if another launch
arrives concurrently. [Apple instance selection](https://developer.apple.com/documentation/appkit/nsworkspace/openconfiguration/createsnewapplicationinstance)

Send a unique value in the new-instance launch environment and require the
reviewed add-in to prove it on the exact returned peer. Keep startup parked
when the application or a vendor launcher fails to carry that value through.
[Guarded initial launch](../../../Changes/Research/Workers/FusionStartup/FusionOwnerColdStart.md)
