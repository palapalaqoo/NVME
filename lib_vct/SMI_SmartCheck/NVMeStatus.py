from Data import *

# -----------------------------Generic Command Status-----------------------------

successfulCompletion = StatusField(0x0)
successfulCompletion.SC, successfulCompletion.SCT = 0x0, 0x0

invalidCommandOpcode = StatusField(0x1)
invalidCommandOpcode.SC, invalidCommandOpcode.SCT = 0x1, 0x0

invalidFieldInCommand = StatusField(0x2)
invalidFieldInCommand.SC, invalidFieldInCommand.SCT = 0x2, 0x0

invalidNamespaceOrFormat = StatusField(0xb)
invalidNamespaceOrFormat.SC, invalidNamespaceOrFormat.SCT = 0xb, 0x0

commandSequenceError = StatusField(0xc)
commandSequenceError.SC, commandSequenceError.SCT = 0xc, 0x0

sanitizeFailed = StatusField(0x1c)
sanitizeFailed.SC, sanitizeFailed.SCT = 0x1c, 0x0

sanitizeInProgress = StatusField(0x1d)
sanitizeInProgress.SC, sanitizeInProgress.SCT = 0x1d, 0x0

LBAOutOfRange = StatusField(0x80)
LBAOutOfRange.SC, LBAOutOfRange.SCT = 0x80, 0x0

capacityExceeded = StatusField(0x81)
capacityExceeded.SC, capacityExceeded.SCT = 0x81, 0x0

namespaceNotReady = StatusField(0x82)
namespaceNotReady.SC, namespaceNotReady.SCT = 0x82, 0x0

reservationConflict = StatusField(0x83)
reservationConflict.SC, reservationConflict.SCT = 0x83, 0x0

formatInProgress = StatusField(0x84)
formatInProgress.SC, formatInProgress.SCT = 0x84, 0x0

# ----------------------------Command Specific Status-----------------------------

completionQueueInvalid = StatusField(0x100)
completionQueueInvalid.SC, completionQueueInvalid.SCT = 0x0, 0x1

invalidQueueIdentifier = StatusField(0x101)
invalidQueueIdentifier.SC, invalidQueueIdentifier.SCT = 0x1, 0x1

invalidQueueSize = StatusField(0x102)
invalidQueueSize.SC, invalidQueueSize.SCT = 0x2, 0x1

abortCommandLimitExceeded = StatusField(0x103)
abortCommandLimitExceeded.SC, abortCommandLimitExceeded.SCT = 0x3, 0x1

asynchronousEventRequestLimitExceeded = StatusField(0x105)
asynchronousEventRequestLimitExceeded.SC, asynchronousEventRequestLimitExceeded.SCT = 0x5, 0x1

invalidFirmwareSlot = StatusField(0x106)
invalidFirmwareSlot.SC, invalidFirmwareSlot.SCT = 0x6, 0x1

invalidFirmwareImage = StatusField(0x107)
invalidFirmwareImage.SC, invalidFirmwareImage.SCT = 0x7, 0x1

invalidInterruptVector = StatusField(0x108)
invalidInterruptVector.SC, invalidInterruptVector.SCT = 0x8, 0x1

invalidLogPage = StatusField(0x109)
invalidLogPage.SC, invalidLogPage.SCT = 0x9, 0x1

invalidFormat = StatusField(0x10a)
invalidFormat.SC, invalidFormat.SCT = 0xa, 0x1

firmwareActivationRequiresConventionalReset = StatusField(0x10b)
firmwareActivationRequiresConventionalReset.SC, firmwareActivationRequiresConventionalReset.SCT = 0xb, 0x1

invalidQueueDeletion = StatusField(0x10c)
invalidQueueDeletion.SC, invalidQueueDeletion.SCT = 0xc, 0x1

featureIdentifierNotSaveable = StatusField(0x10d)
featureIdentifierNotSaveable.SC, featureIdentifierNotSaveable.SCT = 0xd, 0x1

featureNotChangeable = StatusField(0x10e)
featureNotChangeable.SC, featureNotChangeable.SCT = 0xe, 0x1

featureNotNamespaceSpecific = StatusField(0x10f)
featureNotNamespaceSpecific.SC, featureNotNamespaceSpecific.SCT = 0xf, 0x1

firmwareActivationRequiresNVMSubsystemReset = StatusField(0x110)
firmwareActivationRequiresNVMSubsystemReset.SC, firmwareActivationRequiresNVMSubsystemReset.SCT = 0x10, 0x1

firmwareActivationRequiresReset = StatusField(0x111)
firmwareActivationRequiresReset.SC, firmwareActivationRequiresReset.SCT = 0x11, 0x1

firmwareActivationRequiresMaximumTimeViolation = StatusField(0x112)
firmwareActivationRequiresMaximumTimeViolation.SC, firmwareActivationRequiresMaximumTimeViolation.SCT = 0x12, 0x1

firmwareActivationProhibited = StatusField(0x113)
firmwareActivationProhibited.SC, firmwareActivationProhibited.SCT = 0x13, 0x1

overlappingRange = StatusField(0x114)
overlappingRange.SC, overlappingRange.SCT = 0x14, 0x1

namespaceInsufficientCapacity = StatusField(0x115)
namespaceInsufficientCapacity.SC, namespaceInsufficientCapacity.SCT = 0x15, 0x1

namespaceIdentifierUnavailable = StatusField(0x116)
namespaceIdentifierUnavailable.SC, namespaceIdentifierUnavailable.SCT = 0x16, 0x1

namespaceAlreadyAttached = StatusField(0x118)
namespaceAlreadyAttached.SC, namespaceAlreadyAttached.SCT = 0x18, 0x1

namespaceIsPrivate = StatusField(0x119)
namespaceIsPrivate.SC, namespaceIsPrivate.SCT = 0x19, 0x1

namespaceNotAttached = StatusField(0x11a)
namespaceNotAttached.SC, namespaceNotAttached.SCT = 0x1a, 0x1

thinProvisioningNotSupported = StatusField(0x11b)
thinProvisioningNotSupported.SC, thinProvisioningNotSupported.SCT = 0x1b, 0x1

controllerListInvalid = StatusField(0x11c)
controllerListInvalid.SC, controllerListInvalid.SCT = 0x1c, 0x1

deviceSelfTestInProgress = StatusField(0x11d)
deviceSelfTestInProgress.SC, deviceSelfTestInProgress.SCT = 0x1d, 0x1

# ------------------------Media and Data Integrity Errors-------------------------

writeFault = StatusField(0x280)
writeFault.SC, writeFault.SCT = 0x80, 0x2

unrecoveredReadError = StatusField(0x281)
unrecoveredReadError.SC, unrecoveredReadError.SCT = 0x81, 0x2

endToEndGuardCheckError = StatusField(0x282)
endToEndGuardCheckError.SC, endToEndGuardCheckError.SCT = 0x82, 0x2

endToEndApplicationTagCheckError = StatusField(0x283)
endToEndApplicationTagCheckError.SC, endToEndApplicationTagCheckError.SCT = 0x83, 0x2

endToEndReferenceTagCheckError = StatusField(0x284)
endToEndReferenceTagCheckError.SC, endToEndReferenceTagCheckError.SCT = 0x84, 0x2

compareFailure = StatusField(0x285)
compareFailure.SC, compareFailure.SCT = 0x85, 0x2

accessDenied = StatusField(0x286)
accessDenied.SC, accessDenied.SCT = 0x86, 0x2

deallocatedOrUnwrittenLogicalBlock = StatusField(0x287)
deallocatedOrUnwrittenLogicalBlock.SC, deallocatedOrUnwrittenLogicalBlock.SCT = 0x87, 0x2