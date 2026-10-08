from typing import Protocol, Optional, TypeVar, Generic, no_type_check
from dataclasses import dataclass

A = TypeVar("A")
B = TypeVar("B")


@dataclass
class Symbol(Generic[A, B]):
    # Either a list of at least one address or None if not defined for the region.
    addresses: A
    # Like addresses but memory-absolute
    absolute_addresses: A
    # None for most functions. Data fields should generally have a length defined.
    length: B
    name: str
    description: str
    # C type of this symbol. Empty string if unknown. None for functions.
    c_type: Optional[str]

    @property
    @no_type_check
    def address(self) -> int:
        """First / main address. Raises an IndexError/TypeError if no address is defined."""
        return self.addresses[0]

    @property
    @no_type_check
    def absolute_address(self) -> int:
        """First / main address (absolute). Raises an IndexError/TypeError if no address is defined."""
        return self.absolute_addresses[0]


T = TypeVar("T")
U = TypeVar("U")
L = TypeVar("L")


class SectionProtocol(Protocol[T, U, L]):
    name: str
    description: str
    loadaddress: L
    length: int
    functions: T
    data: U


class Arm7FunctionsProtocol(Protocol):

    _start_arm7: Symbol[
        Optional[list[int]],
        None,
    ]

    do_autoload_arm7: Symbol[
        Optional[list[int]],
        None,
    ]

    StartAutoloadDoneCallbackArm7: Symbol[
        Optional[list[int]],
        None,
    ]

    NitroSpMain: Symbol[
        Optional[list[int]],
        None,
    ]

    HardwareInterrupt: Symbol[
        Optional[list[int]],
        None,
    ]

    ReturnFromInterrupt: Symbol[
        Optional[list[int]],
        None,
    ]

    AudioInterrupt: Symbol[
        Optional[list[int]],
        None,
    ]

    ClearImeFlag: Symbol[
        Optional[list[int]],
        None,
    ]

    ClearIeFlag: Symbol[
        Optional[list[int]],
        None,
    ]

    GetCurrentPlaybackTime: Symbol[
        Optional[list[int]],
        None,
    ]

    ClearIrqFlag: Symbol[
        Optional[list[int]],
        None,
    ]

    EnableIrqFlag: Symbol[
        Optional[list[int]],
        None,
    ]

    SetIrqFlag: Symbol[
        Optional[list[int]],
        None,
    ]

    EnableIrqFiqFlags: Symbol[
        Optional[list[int]],
        None,
    ]

    SetIrqFiqFlags: Symbol[
        Optional[list[int]],
        None,
    ]

    GetProcessorMode: Symbol[
        Optional[list[int]],
        None,
    ]

    _s32_div_f: Symbol[
        Optional[list[int]],
        None,
    ]

    _u32_div_f: Symbol[
        Optional[list[int]],
        None,
    ]

    _u32_div_not_0_f: Symbol[
        Optional[list[int]],
        None,
    ]


class Arm7DataProtocol(Protocol):

    pass


Arm7Protocol = SectionProtocol[
    Arm7FunctionsProtocol,
    Arm7DataProtocol,
    Optional[int],
]


class Arm9FunctionsProtocol(Protocol):

    Svc_SoftReset: Symbol[
        Optional[list[int]],
        None,
    ]

    Svc_WaitByLoop: Symbol[
        Optional[list[int]],
        None,
    ]

    Svc_CpuSet: Symbol[
        Optional[list[int]],
        None,
    ]

    _start: Symbol[
        Optional[list[int]],
        None,
    ]

    InitI_CpuClear32: Symbol[
        Optional[list[int]],
        None,
    ]

    MIi_UncompressBackward: Symbol[
        Optional[list[int]],
        None,
    ]

    do_autoload: Symbol[
        Optional[list[int]],
        None,
    ]

    StartAutoloadDoneCallback: Symbol[
        Optional[list[int]],
        None,
    ]

    init_cp15: Symbol[
        Optional[list[int]],
        None,
    ]

    OSi_ReferSymbol: Symbol[
        Optional[list[int]],
        None,
    ]

    NitroMain: Symbol[
        Optional[list[int]],
        None,
    ]

    InitMemAllocTable: Symbol[
        Optional[list[int]],
        None,
    ]

    SetMemAllocatorParams: Symbol[
        Optional[list[int]],
        None,
    ]

    GetAllocArenaDefault: Symbol[
        Optional[list[int]],
        None,
    ]

    GetFreeArenaDefault: Symbol[
        Optional[list[int]],
        None,
    ]

    InitMemArena: Symbol[
        Optional[list[int]],
        None,
    ]

    MemAllocFlagsToBlockType: Symbol[
        Optional[list[int]],
        None,
    ]

    FindAvailableMemBlock: Symbol[
        Optional[list[int]],
        None,
    ]

    SplitMemBlock: Symbol[
        Optional[list[int]],
        None,
    ]

    MemAlloc: Symbol[
        Optional[list[int]],
        None,
    ]

    MemFree: Symbol[
        Optional[list[int]],
        None,
    ]

    MemArenaAlloc: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateMemArena: Symbol[
        Optional[list[int]],
        None,
    ]

    MemLocateSet: Symbol[
        Optional[list[int]],
        None,
    ]

    MemLocateUnset: Symbol[
        Optional[list[int]],
        None,
    ]

    RoundUpDiv256: Symbol[
        Optional[list[int]],
        None,
    ]

    UFixedPoint64CmpLt: Symbol[
        Optional[list[int]],
        None,
    ]

    MultiplyByFixedPoint: Symbol[
        Optional[list[int]],
        None,
    ]

    UMultiplyByFixedPoint: Symbol[
        Optional[list[int]],
        None,
    ]

    IntToFixedPoint64: Symbol[
        Optional[list[int]],
        None,
    ]

    FixedPoint64ToInt: Symbol[
        Optional[list[int]],
        None,
    ]

    FixedPoint32To64: Symbol[
        Optional[list[int]],
        None,
    ]

    NegateFixedPoint64: Symbol[
        Optional[list[int]],
        None,
    ]

    FixedPoint64IsZero: Symbol[
        Optional[list[int]],
        None,
    ]

    FixedPoint64IsNegative: Symbol[
        Optional[list[int]],
        None,
    ]

    FixedPoint64CmpLt: Symbol[
        Optional[list[int]],
        None,
    ]

    MultiplyFixedPoint64: Symbol[
        Optional[list[int]],
        None,
    ]

    DivideFixedPoint64: Symbol[
        Optional[list[int]],
        None,
    ]

    UMultiplyFixedPoint64: Symbol[
        Optional[list[int]],
        None,
    ]

    UDivideFixedPoint64: Symbol[
        Optional[list[int]],
        None,
    ]

    AddFixedPoint64: Symbol[
        Optional[list[int]],
        None,
    ]

    ClampedLn: Symbol[
        Optional[list[int]],
        None,
    ]

    GetRngSeed: Symbol[
        Optional[list[int]],
        None,
    ]

    SetRngSeed: Symbol[
        Optional[list[int]],
        None,
    ]

    Rand16Bit: Symbol[
        Optional[list[int]],
        None,
    ]

    RandInt: Symbol[
        Optional[list[int]],
        None,
    ]

    RandRange: Symbol[
        Optional[list[int]],
        None,
    ]

    Rand32Bit: Symbol[
        Optional[list[int]],
        None,
    ]

    RandIntSafe: Symbol[
        Optional[list[int]],
        None,
    ]

    RandRangeSafe: Symbol[
        Optional[list[int]],
        None,
    ]

    WaitForever: Symbol[
        Optional[list[int]],
        None,
    ]

    InterruptMasterDisable: Symbol[
        Optional[list[int]],
        None,
    ]

    InterruptMasterEnable: Symbol[
        Optional[list[int]],
        None,
    ]

    InitMemAllocTableVeneer: Symbol[
        Optional[list[int]],
        None,
    ]

    ZInit8: Symbol[
        Optional[list[int]],
        None,
    ]

    PointsToZero: Symbol[
        Optional[list[int]],
        None,
    ]

    MemZero: Symbol[
        Optional[list[int]],
        None,
    ]

    MemZero16: Symbol[
        Optional[list[int]],
        None,
    ]

    MemZero32: Symbol[
        Optional[list[int]],
        None,
    ]

    MemsetSimple: Symbol[
        Optional[list[int]],
        None,
    ]

    Memset32: Symbol[
        Optional[list[int]],
        None,
    ]

    MemcpySimple: Symbol[
        Optional[list[int]],
        None,
    ]

    Memcpy16: Symbol[
        Optional[list[int]],
        None,
    ]

    Memcpy32: Symbol[
        Optional[list[int]],
        None,
    ]

    TaskProcBoot: Symbol[
        Optional[list[int]],
        None,
    ]

    EnableAllInterrupts: Symbol[
        Optional[list[int]],
        None,
    ]

    GetTime: Symbol[
        Optional[list[int]],
        None,
    ]

    DisableAllInterrupts: Symbol[
        Optional[list[int]],
        None,
    ]

    SoundResume: Symbol[
        Optional[list[int]],
        None,
    ]

    CardPullOutWithStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    CardPullOut: Symbol[
        Optional[list[int]],
        None,
    ]

    CardBackupError: Symbol[
        Optional[list[int]],
        None,
    ]

    HaltProcessDisp: Symbol[
        Optional[list[int]],
        None,
    ]

    OverlayIsLoaded: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadOverlay: Symbol[
        Optional[list[int]],
        None,
    ]

    UnloadOverlay: Symbol[
        Optional[list[int]],
        None,
    ]

    GetDsFirmwareUserSettingsVeneer: Symbol[
        Optional[list[int]],
        None,
    ]

    Rgb8ToRgb5: Symbol[
        Optional[list[int]],
        None,
    ]

    EuclideanNorm: Symbol[
        Optional[list[int]],
        None,
    ]

    ClampComponentAbs: Symbol[
        Optional[list[int]],
        None,
    ]

    GetHeldButtons: Symbol[
        Optional[list[int]],
        None,
    ]

    GetPressedButtons: Symbol[
        Optional[list[int]],
        None,
    ]

    GetReleasedStylus: Symbol[
        Optional[list[int]],
        None,
    ]

    KeyWaitInit: Symbol[
        Optional[list[int]],
        None,
    ]

    DebugPrintSystemClock: Symbol[
        Optional[list[int]],
        None,
    ]

    GetSystemClock: Symbol[
        Optional[list[int]],
        None,
    ]

    SprintfSystemClock: Symbol[
        Optional[list[int]],
        None,
    ]

    DataTransferInit: Symbol[
        Optional[list[int]],
        None,
    ]

    DataTransferStop: Symbol[
        Optional[list[int]],
        None,
    ]

    FileInitVeneer: Symbol[
        Optional[list[int]],
        None,
    ]

    FileOpen: Symbol[
        Optional[list[int]],
        None,
    ]

    FileGetSize: Symbol[
        Optional[list[int]],
        None,
    ]

    FileRead: Symbol[
        Optional[list[int]],
        None,
    ]

    FileSeek: Symbol[
        Optional[list[int]],
        None,
    ]

    FileClose: Symbol[
        Optional[list[int]],
        None,
    ]

    UnloadFile: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadFileFromRom: Symbol[
        Optional[list[int]],
        None,
    ]

    TransformPaletteDataWithFlushDivideFade: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateFadeStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    HandleFades: Symbol[
        Optional[list[int]],
        None,
    ]

    GetFadeStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    InitDebug: Symbol[
        Optional[list[int]],
        None,
    ]

    InitDebugFlag: Symbol[
        Optional[list[int]],
        None,
    ]

    GetDebugFlag: Symbol[
        Optional[list[int]],
        None,
    ]

    SetDebugFlag: Symbol[
        Optional[list[int]],
        None,
    ]

    InitDebugStripped6: Symbol[
        Optional[list[int]],
        None,
    ]

    AppendProgPos: Symbol[
        Optional[list[int]],
        None,
    ]

    InitDebugStripped5: Symbol[
        Optional[list[int]],
        None,
    ]

    DebugPrintTrace: Symbol[
        Optional[list[int]],
        None,
    ]

    DebugDisplay: Symbol[
        Optional[list[int]],
        None,
    ]

    DebugPrint0: Symbol[
        Optional[list[int]],
        None,
    ]

    InitDebugLogFlag: Symbol[
        Optional[list[int]],
        None,
    ]

    GetDebugLogFlag: Symbol[
        Optional[list[int]],
        None,
    ]

    SetDebugLogFlag: Symbol[
        Optional[list[int]],
        None,
    ]

    DebugPrint: Symbol[
        Optional[list[int]],
        None,
    ]

    InitDebugStripped4: Symbol[
        Optional[list[int]],
        None,
    ]

    InitDebugStripped3: Symbol[
        Optional[list[int]],
        None,
    ]

    InitDebugStripped2: Symbol[
        Optional[list[int]],
        None,
    ]

    InitDebugStripped1: Symbol[
        Optional[list[int]],
        None,
    ]

    FatalError: Symbol[
        Optional[list[int]],
        None,
    ]

    OpenAllPackFiles: Symbol[
        Optional[list[int]],
        None,
    ]

    GetFileLengthInPackWithPackNb: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadFileInPackWithPackId: Symbol[
        Optional[list[int]],
        None,
    ]

    AllocAndLoadFileInPack: Symbol[
        Optional[list[int]],
        None,
    ]

    OpenPackFile: Symbol[
        Optional[list[int]],
        None,
    ]

    GetFileLengthInPack: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadFileInPack: Symbol[
        Optional[list[int]],
        None,
    ]

    GetDungeonResultMsg: Symbol[
        Optional[list[int]],
        None,
    ]

    GetDamageSource: Symbol[
        Optional[list[int]],
        None,
    ]

    GetItemCategoryVeneer: Symbol[
        Optional[list[int]],
        None,
    ]

    GetItemMoveId16: Symbol[
        Optional[list[int]],
        None,
    ]

    IsThrownItem: Symbol[
        Optional[list[int]],
        None,
    ]

    IsNotMoney: Symbol[
        Optional[list[int]],
        None,
    ]

    IsEdible: Symbol[
        Optional[list[int]],
        None,
    ]

    IsHM: Symbol[
        Optional[list[int]],
        None,
    ]

    IsGummi: Symbol[
        Optional[list[int]],
        None,
    ]

    IsAuraBow: Symbol[
        Optional[list[int]],
        None,
    ]

    IsLosableItem: Symbol[
        Optional[list[int]],
        None,
    ]

    IsTreasureBox: Symbol[
        Optional[list[int]],
        None,
    ]

    IsStorableItem: Symbol[
        Optional[list[int]],
        None,
    ]

    IsShoppableItem: Symbol[
        Optional[list[int]],
        None,
    ]

    IsValidTargetItem: Symbol[
        Optional[list[int]],
        None,
    ]

    IsItemUsableNow: Symbol[
        Optional[list[int]],
        None,
    ]

    IsTicketItem: Symbol[
        Optional[list[int]],
        None,
    ]

    InitItem: Symbol[
        Optional[list[int]],
        None,
    ]

    InitStandardItem: Symbol[
        Optional[list[int]],
        None,
    ]

    InitBulkItem: Symbol[
        Optional[list[int]],
        None,
    ]

    BulkItemToItem: Symbol[
        Optional[list[int]],
        None,
    ]

    ItemToBulkItem: Symbol[
        Optional[list[int]],
        None,
    ]

    GetDisplayedBuyPrice: Symbol[
        Optional[list[int]],
        None,
    ]

    GetDisplayedSellPrice: Symbol[
        Optional[list[int]],
        None,
    ]

    GetActualBuyPrice: Symbol[
        Optional[list[int]],
        None,
    ]

    GetActualSellPrice: Symbol[
        Optional[list[int]],
        None,
    ]

    FindItemInInventory: Symbol[
        Optional[list[int]],
        None,
    ]

    SprintfStatic: Symbol[
        Optional[list[int]],
        None,
    ]

    ItemZInit: Symbol[
        Optional[list[int]],
        None,
    ]

    AreItemsEquivalent: Symbol[
        Optional[list[int]],
        None,
    ]

    WriteItemsToSave: Symbol[
        Optional[list[int]],
        None,
    ]

    ReadItemsFromSave: Symbol[
        Optional[list[int]],
        None,
    ]

    IsItemAvailableInDungeonGroup: Symbol[
        Optional[list[int]],
        None,
    ]

    GetItemIdFromList: Symbol[
        Optional[list[int]],
        None,
    ]

    NormalizeTreasureBox: Symbol[
        Optional[list[int]],
        None,
    ]

    SortItemList: Symbol[
        Optional[list[int]],
        None,
    ]

    RemoveEmptyItems: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadItemPspi2n: Symbol[
        Optional[list[int]],
        None,
    ]

    GetExclusiveItemType: Symbol[
        Optional[list[int]],
        None,
    ]

    GetExclusiveItemOffsetEnsureValid: Symbol[
        Optional[list[int]],
        None,
    ]

    IsItemValid: Symbol[
        Optional[list[int]],
        None,
    ]

    GetExclusiveItemParameter: Symbol[
        Optional[list[int]],
        None,
    ]

    GetItemCategory: Symbol[
        Optional[list[int]],
        None,
    ]

    EnsureValidItem: Symbol[
        Optional[list[int]],
        None,
    ]

    GetItemName: Symbol[
        Optional[list[int]],
        None,
    ]

    GetItemNameFormatted: Symbol[
        Optional[list[int]],
        None,
    ]

    GetItemBuyPrice: Symbol[
        Optional[list[int]],
        None,
    ]

    GetItemSellPrice: Symbol[
        Optional[list[int]],
        None,
    ]

    GetItemSpriteId: Symbol[
        Optional[list[int]],
        None,
    ]

    GetItemPaletteId: Symbol[
        Optional[list[int]],
        None,
    ]

    GetItemActionName: Symbol[
        Optional[list[int]],
        None,
    ]

    GetThrownItemQuantityLimit: Symbol[
        Optional[list[int]],
        None,
    ]

    GetItemMoveId: Symbol[
        Optional[list[int]],
        None,
    ]

    TestItemAiFlag: Symbol[
        Optional[list[int]],
        None,
    ]

    IsItemInTimeDarkness: Symbol[
        Optional[list[int]],
        None,
    ]

    IsItemValidVeneer: Symbol[
        Optional[list[int]],
        None,
    ]

    SetActiveInventoryToMain: Symbol[
        Optional[list[int]],
        None,
    ]

    AllInventoriesZInit: Symbol[
        Optional[list[int]],
        None,
    ]

    SpecialEpisodeInventoryZInit: Symbol[
        Optional[list[int]],
        None,
    ]

    RescueInventoryZInit: Symbol[
        Optional[list[int]],
        None,
    ]

    SetActiveInventory: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMoneyCarried: Symbol[
        Optional[list[int]],
        None,
    ]

    SetMoneyCarried: Symbol[
        Optional[list[int]],
        None,
    ]

    AddMoneyCarried: Symbol[
        Optional[list[int]],
        None,
    ]

    GetCurrentBagCapacity: Symbol[
        Optional[list[int]],
        None,
    ]

    IsBagFull: Symbol[
        Optional[list[int]],
        None,
    ]

    GetNbItemsInBag: Symbol[
        Optional[list[int]],
        None,
    ]

    CountNbItemsOfTypeInBag: Symbol[
        Optional[list[int]],
        None,
    ]

    CountItemTypeInBag: Symbol[
        Optional[list[int]],
        None,
    ]

    IsItemInBag: Symbol[
        Optional[list[int]],
        None,
    ]

    IsItemWithFlagsInBag: Symbol[
        Optional[list[int]],
        None,
    ]

    IsItemInTreasureBoxes: Symbol[
        Optional[list[int]],
        None,
    ]

    IsHeldItemInBag: Symbol[
        Optional[list[int]],
        None,
    ]

    IsItemForSpecialSpawnInBag: Symbol[
        Optional[list[int]],
        None,
    ]

    HasStorableItems: Symbol[
        Optional[list[int]],
        None,
    ]

    GetItemIndex: Symbol[
        Optional[list[int]],
        None,
    ]

    GetEquivItemIndex: Symbol[
        Optional[list[int]],
        None,
    ]

    GetEquippedThrowableItem: Symbol[
        Optional[list[int]],
        None,
    ]

    GetFirstUnequippedItemOfType: Symbol[
        Optional[list[int]],
        None,
    ]

    CopyItemAtIdx: Symbol[
        Optional[list[int]],
        None,
    ]

    GetItemAtIdx: Symbol[
        Optional[list[int]],
        None,
    ]

    RemoveEmptyItemsInBag: Symbol[
        Optional[list[int]],
        None,
    ]

    RemoveItemNoHole: Symbol[
        Optional[list[int]],
        None,
    ]

    RemoveItem: Symbol[
        Optional[list[int]],
        None,
    ]

    RemoveHeldItemNoHole: Symbol[
        Optional[list[int]],
        None,
    ]

    RemoveItemByIdAndStackNoHole: Symbol[
        Optional[list[int]],
        None,
    ]

    RemoveEquivItem: Symbol[
        Optional[list[int]],
        None,
    ]

    RemoveEquivItemNoHole: Symbol[
        Optional[list[int]],
        None,
    ]

    DecrementStackItem: Symbol[
        Optional[list[int]],
        None,
    ]

    RemoveItemNoHoleCheck: Symbol[
        Optional[list[int]],
        None,
    ]

    RemoveFirstUnequippedItemOfType: Symbol[
        Optional[list[int]],
        None,
    ]

    RemoveAllItems: Symbol[
        Optional[list[int]],
        None,
    ]

    RemoveAllItemsStartingAt: Symbol[
        Optional[list[int]],
        None,
    ]

    SpecialProcAddItemToBag: Symbol[
        Optional[list[int]],
        None,
    ]

    AddItemToBagNoHeld: Symbol[
        Optional[list[int]],
        None,
    ]

    AddItemToBag: Symbol[
        Optional[list[int]],
        None,
    ]

    CleanStickyItemsInBag: Symbol[
        Optional[list[int]],
        None,
    ]

    CountStickyItemsInBag: Symbol[
        Optional[list[int]],
        None,
    ]

    TransmuteHeldItemInBag: Symbol[
        Optional[list[int]],
        None,
    ]

    SetFlagsForHeldItemInBag: Symbol[
        Optional[list[int]],
        None,
    ]

    RemoveHolderForItemInBag: Symbol[
        Optional[list[int]],
        None,
    ]

    SetHolderForItemInBag: Symbol[
        Optional[list[int]],
        None,
    ]

    SortItemsInBag: Symbol[
        Optional[list[int]],
        None,
    ]

    RemovePokeItemsInBag: Symbol[
        Optional[list[int]],
        None,
    ]

    IsStorageFull: Symbol[
        Optional[list[int]],
        None,
    ]

    CountNbOfItemsInStorage: Symbol[
        Optional[list[int]],
        None,
    ]

    CountNbOfValidItemsInStorage: Symbol[
        Optional[list[int]],
        None,
    ]

    CountNbOfValidItemsInTimeDarknessInStorage: Symbol[
        Optional[list[int]],
        None,
    ]

    CountNbItemsOfTypeInStorage: Symbol[
        Optional[list[int]],
        None,
    ]

    CountItemTypeInStorage: Symbol[
        Optional[list[int]],
        None,
    ]

    GetEquivBulkItemIdxInStorage: Symbol[
        Optional[list[int]],
        None,
    ]

    ConvertStorageItemAtIdxToBulkItem: Symbol[
        Optional[list[int]],
        None,
    ]

    ConvertStorageItemAtIdxToItem: Symbol[
        Optional[list[int]],
        None,
    ]

    RemoveItemAtIdxInStorage: Symbol[
        Optional[list[int]],
        None,
    ]

    RemoveBulkItemInStorage: Symbol[
        Optional[list[int]],
        None,
    ]

    RemoveItemInStorage: Symbol[
        Optional[list[int]],
        None,
    ]

    StorageZInit: Symbol[
        Optional[list[int]],
        None,
    ]

    AddBulkItemToStorage: Symbol[
        Optional[list[int]],
        None,
    ]

    AddItemToStorage: Symbol[
        Optional[list[int]],
        None,
    ]

    SortItemsInStorage: Symbol[
        Optional[list[int]],
        None,
    ]

    AllKecleonShopsZInit: Symbol[
        Optional[list[int]],
        None,
    ]

    SpecialEpisodeKecleonShopZInit: Symbol[
        Optional[list[int]],
        None,
    ]

    SetActiveKecleonShop: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMoneyStored: Symbol[
        Optional[list[int]],
        None,
    ]

    SetMoneyStored: Symbol[
        Optional[list[int]],
        None,
    ]

    AddMoneyStored: Symbol[
        Optional[list[int]],
        None,
    ]

    SortKecleonItems1: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateKecleonItems1: Symbol[
        Optional[list[int]],
        None,
    ]

    SortKecleonItems2: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateKecleonItems2: Symbol[
        Optional[list[int]],
        None,
    ]

    GetExclusiveItemOffset: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyExclusiveItemStatBoosts: Symbol[
        Optional[list[int]],
        None,
    ]

    SetExclusiveItemEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ExclusiveItemEffectFlagTest: Symbol[
        Optional[list[int]],
        None,
    ]

    IsExclusiveItemIdForMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    IsExclusiveItemForMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    BagHasExclusiveItemTypeForMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    GetExclusiveItemForMonsterFromBag: Symbol[
        Optional[list[int]],
        None,
    ]

    GetHpBoostFromExclusiveItems: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyGummiBoostsToGroundMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyGummiBoostsToTeamMember: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplySitrusBerryBoostToGroundMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyLifeSeedBoostToGroundMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyGinsengToGroundMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyProteinBoostToGroundMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyCalciumBoostToGroundMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyIronBoostToGroundMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyZincBoostToGroundMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyNectarBoostToGroundMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    IsMonsterAffectedByGravelyrockGroundMode: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyGravelyrockBoostToGroundMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyGummiBoostsGroundMode: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadSynthBin: Symbol[
        Optional[list[int]],
        None,
    ]

    CloseSynthBin: Symbol[
        Optional[list[int]],
        None,
    ]

    GetSynthItem: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadWazaP: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadWazaP2: Symbol[
        Optional[list[int]],
        None,
    ]

    UnloadCurrentWazaP: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMoveName: Symbol[
        Optional[list[int]],
        None,
    ]

    FormatMoveString: Symbol[
        Optional[list[int]],
        None,
    ]

    FormatMoveStringMore: Symbol[
        Optional[list[int]],
        None,
    ]

    InitMove: Symbol[
        Optional[list[int]],
        None,
    ]

    InitMoveCheckId: Symbol[
        Optional[list[int]],
        None,
    ]

    GetInfoMoveGround: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMoveTargetAndRange: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMoveType: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMovesetLevelUpPtr: Symbol[
        Optional[list[int]],
        None,
    ]

    IsInvalidMoveset: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMovesetHmTmPtr: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMovesetEggPtr: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMoveAiWeight: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMoveNbStrikes: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMoveBasePower: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMoveBasePowerGround: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMoveAccuracyOrAiChance: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMoveBasePp: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMaxPp: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMoveMaxGinsengBoost: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMoveMaxGinsengBoostGround: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMoveCritChance: Symbol[
        Optional[list[int]],
        None,
    ]

    IsThawingMove: Symbol[
        Optional[list[int]],
        None,
    ]

    IsAffectedByTaunt: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMoveRangeId: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMoveActualAccuracy: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMoveBasePowerFromId: Symbol[
        Optional[list[int]],
        None,
    ]

    IsMoveRangeString19: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMoveMessageFromId: Symbol[
        Optional[list[int]],
        None,
    ]

    GetNbMoves: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMovesetIdx: Symbol[
        Optional[list[int]],
        None,
    ]

    IsReflectedByMagicCoat: Symbol[
        Optional[list[int]],
        None,
    ]

    CanBeSnatched: Symbol[
        Optional[list[int]],
        None,
    ]

    FailsWhileMuzzled: Symbol[
        Optional[list[int]],
        None,
    ]

    IsSoundMove: Symbol[
        Optional[list[int]],
        None,
    ]

    IsRecoilMove: Symbol[
        Optional[list[int]],
        None,
    ]

    AllManip1: Symbol[
        Optional[list[int]],
        None,
    ]

    AllManip2: Symbol[
        Optional[list[int]],
        None,
    ]

    ManipMoves1v1: Symbol[
        Optional[list[int]],
        None,
    ]

    ManipMoves1v2: Symbol[
        Optional[list[int]],
        None,
    ]

    ManipMoves2v1: Symbol[
        Optional[list[int]],
        None,
    ]

    ManipMoves2v2: Symbol[
        Optional[list[int]],
        None,
    ]

    DungeonMoveToGroundMove: Symbol[
        Optional[list[int]],
        None,
    ]

    GroundToDungeonMoveset: Symbol[
        Optional[list[int]],
        None,
    ]

    DungeonToGroundMoveset: Symbol[
        Optional[list[int]],
        None,
    ]

    GetInfoGroundMoveset: Symbol[
        Optional[list[int]],
        None,
    ]

    FindFirstFreeMovesetIdx: Symbol[
        Optional[list[int]],
        None,
    ]

    LearnMoves: Symbol[
        Optional[list[int]],
        None,
    ]

    CopyMoveTo: Symbol[
        Optional[list[int]],
        None,
    ]

    CopyMoveFrom: Symbol[
        Optional[list[int]],
        None,
    ]

    CopyMovesetTo: Symbol[
        Optional[list[int]],
        None,
    ]

    CopyMovesetFrom: Symbol[
        Optional[list[int]],
        None,
    ]

    Is2TurnsMove: Symbol[
        Optional[list[int]],
        None,
    ]

    IsRegularAttackOrProjectile: Symbol[
        Optional[list[int]],
        None,
    ]

    IsPunchMove: Symbol[
        Optional[list[int]],
        None,
    ]

    IsHealingWishOrLunarDance: Symbol[
        Optional[list[int]],
        None,
    ]

    IsCopyingMove: Symbol[
        Optional[list[int]],
        None,
    ]

    IsTrappingMove: Symbol[
        Optional[list[int]],
        None,
    ]

    IsOneHitKoMove: Symbol[
        Optional[list[int]],
        None,
    ]

    IsNot2TurnsMoveOrSketch: Symbol[
        Optional[list[int]],
        None,
    ]

    IsRealMove: Symbol[
        Optional[list[int]],
        None,
    ]

    IsMovesetValid: Symbol[
        Optional[list[int]],
        None,
    ]

    IsRealMoveInTimeDarkness: Symbol[
        Optional[list[int]],
        None,
    ]

    IsMovesetValidInTimeDarkness: Symbol[
        Optional[list[int]],
        None,
    ]

    GetFirstNotRealMoveInTimeDarkness: Symbol[
        Optional[list[int]],
        None,
    ]

    IsSameMove: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMoveCategory: Symbol[
        Optional[list[int]],
        None,
    ]

    GetPpIncrease: Symbol[
        Optional[list[int]],
        None,
    ]

    OpenWaza: Symbol[
        Optional[list[int]],
        None,
    ]

    SelectWaza: Symbol[
        Optional[list[int]],
        None,
    ]

    PlayBgmByIdVeneer: Symbol[
        Optional[list[int]],
        None,
    ]

    PlayBgmByIdVolumeVeneer: Symbol[
        Optional[list[int]],
        None,
    ]

    PlaySeVolumeWrapper: Symbol[
        Optional[list[int]],
        None,
    ]

    PlayBgmById: Symbol[
        Optional[list[int]],
        None,
    ]

    PlayBgmByIdVolume: Symbol[
        Optional[list[int]],
        None,
    ]

    StopBgmCommand: Symbol[
        Optional[list[int]],
        None,
    ]

    PlaySeByIdVolume: Symbol[
        Optional[list[int]],
        None,
    ]

    SendAudioCommand2: Symbol[
        Optional[list[int]],
        None,
    ]

    AllocAudioCommand: Symbol[
        Optional[list[int]],
        None,
    ]

    SendAudioCommand: Symbol[
        Optional[list[int]],
        None,
    ]

    InitSoundSystem: Symbol[
        Optional[list[int]],
        None,
    ]

    ManipBgmPlayback: Symbol[
        Optional[list[int]],
        None,
    ]

    SoundDriverReset: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadDseFile: Symbol[
        Optional[list[int]],
        None,
    ]

    PlaySeLoad: Symbol[
        Optional[list[int]],
        None,
    ]

    IsSongOver: Symbol[
        Optional[list[int]],
        None,
    ]

    PlayBgm: Symbol[
        Optional[list[int]],
        None,
    ]

    StopBgm: Symbol[
        Optional[list[int]],
        None,
    ]

    ChangeBgm: Symbol[
        Optional[list[int]],
        None,
    ]

    PlayBgm2: Symbol[
        Optional[list[int]],
        None,
    ]

    StopBgm2: Symbol[
        Optional[list[int]],
        None,
    ]

    ChangeBgm2: Symbol[
        Optional[list[int]],
        None,
    ]

    PlayME: Symbol[
        Optional[list[int]],
        None,
    ]

    StopME: Symbol[
        Optional[list[int]],
        None,
    ]

    PlaySe: Symbol[
        Optional[list[int]],
        None,
    ]

    PlaySeFullSpec: Symbol[
        Optional[list[int]],
        None,
    ]

    SeChangeVolume: Symbol[
        Optional[list[int]],
        None,
    ]

    SeChangePan: Symbol[
        Optional[list[int]],
        None,
    ]

    StopSe: Symbol[
        Optional[list[int]],
        None,
    ]

    InitAnimationControl: Symbol[
        Optional[list[int]],
        None,
    ]

    InitAnimationControlWithSet: Symbol[
        Optional[list[int]],
        None,
    ]

    SetSpriteIdForAnimationControl: Symbol[
        Optional[list[int]],
        None,
    ]

    SetAnimationForAnimationControlInternal: Symbol[
        Optional[list[int]],
        None,
    ]

    SetAnimationForAnimationControl: Symbol[
        Optional[list[int]],
        None,
    ]

    GetWanForAnimationControl: Symbol[
        Optional[list[int]],
        None,
    ]

    SetAndPlayAnimationForAnimationControl: Symbol[
        Optional[list[int]],
        None,
    ]

    SwitchAnimationControlToNextFrame: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadAnimationFrameAndIncrementInAnimationControl: Symbol[
        Optional[list[int]],
        None,
    ]

    AnimationControlGetAllocForMaxFrame: Symbol[
        Optional[list[int]],
        None,
    ]

    DeleteWanTableEntry: Symbol[
        Optional[list[int]],
        None,
    ]

    AllocateWanTableEntry: Symbol[
        Optional[list[int]],
        None,
    ]

    FindWanTableEntry: Symbol[
        Optional[list[int]],
        None,
    ]

    GetLoadedWanTableEntry: Symbol[
        Optional[list[int]],
        None,
    ]

    InitWanTable: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadWanTableEntry: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadWanTableEntryFromPack: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadWanTableEntryFromPackUseProvidedMemory: Symbol[
        Optional[list[int]],
        None,
    ]

    ReplaceWanFromBinFile: Symbol[
        Optional[list[int]],
        None,
    ]

    DeleteWanTableEntryVeneer: Symbol[
        Optional[list[int]],
        None,
    ]

    WanHasAnimationGroup: Symbol[
        Optional[list[int]],
        None,
    ]

    WanTableSpriteHasAnimationGroup: Symbol[
        Optional[list[int]],
        None,
    ]

    SpriteTypeInWanTable: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadWteFromRom: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadWteFromFileDirectory: Symbol[
        Optional[list[int]],
        None,
    ]

    UnloadWte: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadWtuFromBin: Symbol[
        Optional[list[int]],
        None,
    ]

    ProcessWte: Symbol[
        Optional[list[int]],
        None,
    ]

    GeomSetTexImageParam: Symbol[
        Optional[list[int]],
        None,
    ]

    GeomSetVertexCoord16: Symbol[
        Optional[list[int]],
        None,
    ]

    InitRender3dData: Symbol[
        Optional[list[int]],
        None,
    ]

    GeomSwapBuffers: Symbol[
        Optional[list[int]],
        None,
    ]

    InitRender3dElement64: Symbol[
        Optional[list[int]],
        None,
    ]

    Render3d64Texture0x7: Symbol[
        Optional[list[int]],
        None,
    ]

    Render3d64WindowFrame: Symbol[
        Optional[list[int]],
        None,
    ]

    EnqueueRender3d64Tiling: Symbol[
        Optional[list[int]],
        None,
    ]

    Render3d64Tiling: Symbol[
        Optional[list[int]],
        None,
    ]

    Render3d64Quadrilateral: Symbol[
        Optional[list[int]],
        None,
    ]

    Render3d64RectangleMulticolor: Symbol[
        Optional[list[int]],
        None,
    ]

    Render3d64Rectangle: Symbol[
        Optional[list[int]],
        None,
    ]

    Render3d64Nothing: Symbol[
        Optional[list[int]],
        None,
    ]

    Render3d64Texture: Symbol[
        Optional[list[int]],
        None,
    ]

    Render3dElement64: Symbol[
        Optional[list[int]],
        None,
    ]

    HandleSir0Translation: Symbol[
        Optional[list[int]],
        None,
    ]

    ConvertPointersSir0: Symbol[
        Optional[list[int]],
        None,
    ]

    HandleSir0TranslationVeneer: Symbol[
        Optional[list[int]],
        None,
    ]

    DecompressAtNormalVeneer: Symbol[
        Optional[list[int]],
        None,
    ]

    DecompressAtNormal: Symbol[
        Optional[list[int]],
        None,
    ]

    DecompressAtHalf: Symbol[
        Optional[list[int]],
        None,
    ]

    DecompressAtFromMemoryPointerVeneer: Symbol[
        Optional[list[int]],
        None,
    ]

    DecompressAtFromMemoryPointer: Symbol[
        Optional[list[int]],
        None,
    ]

    WriteByteFromMemoryPointer: Symbol[
        Optional[list[int]],
        None,
    ]

    GetAtSize: Symbol[
        Optional[list[int]],
        None,
    ]

    GetLanguageType: Symbol[
        Optional[list[int]],
        None,
    ]

    GetLanguage: Symbol[
        Optional[list[int]],
        None,
    ]

    StrcmpTag: Symbol[
        Optional[list[int]],
        None,
    ]

    AtoiTag: Symbol[
        Optional[list[int]],
        None,
    ]

    AnalyzeText: Symbol[
        Optional[list[int]],
        None,
    ]

    PreprocessString: Symbol[
        Optional[list[int]],
        None,
    ]

    PreprocessStringFromId: Symbol[
        Optional[list[int]],
        None,
    ]

    StrcmpTagVeneer: Symbol[
        Optional[list[int]],
        None,
    ]

    AtoiTagVeneer: Symbol[
        Optional[list[int]],
        None,
    ]

    InitPreprocessorArgs: Symbol[
        Optional[list[int]],
        None,
    ]

    SetStringAccuracy: Symbol[
        Optional[list[int]],
        None,
    ]

    SetStringPower: Symbol[
        Optional[list[int]],
        None,
    ]

    GetRankString: Symbol[
        Optional[list[int]],
        None,
    ]

    GetCurrentTeamNameString: Symbol[
        Optional[list[int]],
        None,
    ]

    GetBagNameString: Symbol[
        Optional[list[int]],
        None,
    ]

    GetDungeonResultString: Symbol[
        Optional[list[int]],
        None,
    ]

    SetQuestionMarks: Symbol[
        Optional[list[int]],
        None,
    ]

    StrcpySimple: Symbol[
        Optional[list[int]],
        None,
    ]

    StrncpySimple: Symbol[
        Optional[list[int]],
        None,
    ]

    StrncpySimpleNoPad: Symbol[
        Optional[list[int]],
        None,
    ]

    StrncmpSimple: Symbol[
        Optional[list[int]],
        None,
    ]

    StrncpySimpleNoPadSafe: Symbol[
        Optional[list[int]],
        None,
    ]

    StrcpyName: Symbol[
        Optional[list[int]],
        None,
    ]

    StrncpyName: Symbol[
        Optional[list[int]],
        None,
    ]

    GetStringFromFile: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadStringFile: Symbol[
        Optional[list[int]],
        None,
    ]

    AllocateTemp1024ByteBufferFromPool: Symbol[
        Optional[list[int]],
        None,
    ]

    GetStringFromFileVeneer: Symbol[
        Optional[list[int]],
        None,
    ]

    StringFromId: Symbol[
        Optional[list[int]],
        None,
    ]

    CopyStringFromId: Symbol[
        Optional[list[int]],
        None,
    ]

    CopyNStringFromId: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadTblTalk: Symbol[
        Optional[list[int]],
        None,
    ]

    GetTalkLine: Symbol[
        Optional[list[int]],
        None,
    ]

    IsAOrBPressed: Symbol[
        Optional[list[int]],
        None,
    ]

    DrawTextInWindow: Symbol[
        Optional[list[int]],
        None,
    ]

    GetCharWidth: Symbol[
        Optional[list[int]],
        None,
    ]

    GetColorCodePaletteOffset: Symbol[
        Optional[list[int]],
        None,
    ]

    DrawChar: Symbol[
        Optional[list[int]],
        None,
    ]

    GetWindow: Symbol[
        Optional[list[int]],
        None,
    ]

    NewWindowScreenCheck: Symbol[
        Optional[list[int]],
        None,
    ]

    NewWindow: Symbol[
        Optional[list[int]],
        None,
    ]

    SetScreenWindowsColor: Symbol[
        Optional[list[int]],
        None,
    ]

    SetBothScreensWindowsColor: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateWindow: Symbol[
        Optional[list[int]],
        None,
    ]

    ClearWindow: Symbol[
        Optional[list[int]],
        None,
    ]

    DeleteWindow: Symbol[
        Optional[list[int]],
        None,
    ]

    GetWindowRectangle: Symbol[
        Optional[list[int]],
        None,
    ]

    GetWindowContents: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadCursors: Symbol[
        Optional[list[int]],
        None,
    ]

    InitWindowTrailer: Symbol[
        Optional[list[int]],
        None,
    ]

    Arm9LoadUnkFieldNa0x2029EC8: Symbol[
        Optional[list[int]],
        None,
    ]

    Arm9StoreUnkFieldNa0x2029ED8: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadAlert: Symbol[
        Optional[list[int]],
        None,
    ]

    PrintClearMark: Symbol[
        Optional[list[int]],
        None,
    ]

    PrintBadgeMark: Symbol[
        Optional[list[int]],
        None,
    ]

    PrintMark: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateParentMenuFromStringIds: Symbol[
        Optional[list[int]],
        None,
    ]

    IsEmptyString: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateParentMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateParentMenuWrapper: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateParentMenuInternal: Symbol[
        Optional[list[int]],
        None,
    ]

    ResumeParentMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    SetParentMenuState7: Symbol[
        Optional[list[int]],
        None,
    ]

    CloseParentMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    IsParentMenuActive: Symbol[
        Optional[list[int]],
        None,
    ]

    CheckParentMenuField0x1A0: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateParentMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateSimpleMenuFromStringIds: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateSimpleMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateSimpleMenuInternal: Symbol[
        Optional[list[int]],
        None,
    ]

    ResumeSimpleMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    CloseSimpleMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    IsSimpleMenuActive: Symbol[
        Optional[list[int]],
        None,
    ]

    CheckSimpleMenuField0x1A0: Symbol[
        Optional[list[int]],
        None,
    ]

    GetSimpleMenuField0x1A4: Symbol[
        Optional[list[int]],
        None,
    ]

    GetSimpleMenuResult: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateSimpleMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    SetSimpleMenuField0x1AC: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateAdvancedMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    ResumeAdvancedMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    CloseAdvancedMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    IsAdvancedMenuActive2: Symbol[
        Optional[list[int]],
        None,
    ]

    IsAdvancedMenuActive: Symbol[
        Optional[list[int]],
        None,
    ]

    GetAdvancedMenuCurrentOption: Symbol[
        Optional[list[int]],
        None,
    ]

    GetAdvancedMenuResult: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateAdvancedMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateCollectionMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    SetCollectionMenuField0x1BC: Symbol[
        Optional[list[int]],
        None,
    ]

    SetCollectionMenuWidth: Symbol[
        Optional[list[int]],
        None,
    ]

    CloseCollectionMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    IsCollectionMenuActive: Symbol[
        Optional[list[int]],
        None,
    ]

    SetCollectionMenuField0x1C8: Symbol[
        Optional[list[int]],
        None,
    ]

    SetCollectionMenuField0x1A0: Symbol[
        Optional[list[int]],
        None,
    ]

    SetCollectionMenuField0x1A4: Symbol[
        Optional[list[int]],
        None,
    ]

    SetCollectionMenuVoidFn: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateCollectionMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    SetCollectionMenuField0x1B2: Symbol[
        Optional[list[int]],
        None,
    ]

    IsCollectionMenuState3: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateOptionsMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    CloseOptionsMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    IsOptionsMenuActive: Symbol[
        Optional[list[int]],
        None,
    ]

    CheckOptionsMenuField0x1A4: Symbol[
        Optional[list[int]],
        None,
    ]

    GetOptionsMenuStates: Symbol[
        Optional[list[int]],
        None,
    ]

    GetOptionsMenuResult: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateOptionsMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateDebugMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    CloseDebugMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    IsDebugMenuActive: Symbol[
        Optional[list[int]],
        None,
    ]

    CheckDebugMenuField0x1A4: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateDebugMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateScrollBoxSingle: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateScrollBoxMulti: Symbol[
        Optional[list[int]],
        None,
    ]

    SetScrollBoxState7: Symbol[
        Optional[list[int]],
        None,
    ]

    CloseScrollBox: Symbol[
        Optional[list[int]],
        None,
    ]

    IsScrollBoxActive: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateScrollBox: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateDialogueBox: Symbol[
        Optional[list[int]],
        None,
    ]

    CloseDialogueBox: Symbol[
        Optional[list[int]],
        None,
    ]

    IsDialogueBoxActive: Symbol[
        Optional[list[int]],
        None,
    ]

    ShowStringIdInDialogueBox: Symbol[
        Optional[list[int]],
        None,
    ]

    ShowStringInDialogueBox: Symbol[
        Optional[list[int]],
        None,
    ]

    ShowDialogueBox: Symbol[
        Optional[list[int]],
        None,
    ]

    ReadStringFromDialogueBox: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateDialogueBox: Symbol[
        Optional[list[int]],
        None,
    ]

    CreatePortraitBox: Symbol[
        Optional[list[int]],
        None,
    ]

    ClosePortraitBox: Symbol[
        Optional[list[int]],
        None,
    ]

    PortraitBoxNeedsUpdate: Symbol[
        Optional[list[int]],
        None,
    ]

    ShowPortraitInPortraitBox: Symbol[
        Optional[list[int]],
        None,
    ]

    HidePortraitBox: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdatePortraitBox: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateTextBox: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateTextBoxWithArg: Symbol[
        Optional[list[int]],
        None,
    ]

    CloseTextBox: Symbol[
        Optional[list[int]],
        None,
    ]

    CloseTextBox2: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateTextBoxInternal: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateTextBox: Symbol[
        Optional[list[int]],
        None,
    ]

    IsTextBoxActive: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateAreaNameBox: Symbol[
        Optional[list[int]],
        None,
    ]

    SetAreaNameBoxState3: Symbol[
        Optional[list[int]],
        None,
    ]

    CloseAreaNameBox: Symbol[
        Optional[list[int]],
        None,
    ]

    IsAreaNameBoxActive: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateAreaNameBox: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateControlsChart: Symbol[
        Optional[list[int]],
        None,
    ]

    CloseControlsChart: Symbol[
        Optional[list[int]],
        None,
    ]

    IsControlsChartActive: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateControlsChart: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateAlertBox: Symbol[
        Optional[list[int]],
        None,
    ]

    CloseAlertBox: Symbol[
        Optional[list[int]],
        None,
    ]

    IsAlertBoxActive: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateAlertBox: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateAdvancedTextBox: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateAdvancedTextBoxWithArg: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateAdvancedTextBoxInternal: Symbol[
        Optional[list[int]],
        None,
    ]

    SetAdvancedTextBoxPartialMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    SetAdvancedTextBoxField0x1C4: Symbol[
        Optional[list[int]],
        None,
    ]

    SetAdvancedTextBoxField0x1C2: Symbol[
        Optional[list[int]],
        None,
    ]

    CloseAdvancedTextBox2: Symbol[
        Optional[list[int]],
        None,
    ]

    SetAdvancedTextBoxState5: Symbol[
        Optional[list[int]],
        None,
    ]

    CloseAdvancedTextBox: Symbol[
        Optional[list[int]],
        None,
    ]

    IsAdvancedTextBoxActive: Symbol[
        Optional[list[int]],
        None,
    ]

    GetAdvancedTextBoxFlags2: Symbol[
        Optional[list[int]],
        None,
    ]

    SetUnkAdvancedTextBoxFn: Symbol[
        Optional[list[int]],
        None,
    ]

    SetUnkAdvancedTextBoxWindowFn: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateAdvancedTextBox: Symbol[
        Optional[list[int]],
        None,
    ]

    PlayAdvancedTextBoxInputSound: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateTeamSelectionMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    CloseTeamSelectionMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    IsTeamSelectionMenuActive: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateTeamSelectionMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    IsTeamSelectionMenuState3: Symbol[
        Optional[list[int]],
        None,
    ]

    CalcMenuHeightDiv8: Symbol[
        Optional[list[int]],
        None,
    ]

    InitWindowInput: Symbol[
        Optional[list[int]],
        None,
    ]

    IsMenuOptionActive: Symbol[
        Optional[list[int]],
        None,
    ]

    PlayWindowInputSound: Symbol[
        Optional[list[int]],
        None,
    ]

    InitInventoryMenuInput: Symbol[
        Optional[list[int]],
        None,
    ]

    ShowKeyboard: Symbol[
        Optional[list[int]],
        None,
    ]

    GetKeyboardStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    GetKeyboardStringResult: Symbol[
        Optional[list[int]],
        None,
    ]

    TeamSelectionMenuGetItem: Symbol[
        Optional[list[int]],
        None,
    ]

    PrintMoveOptionMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    PrintIqSkillsMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    GetNotifyNote: Symbol[
        Optional[list[int]],
        None,
    ]

    SetNotifyNote: Symbol[
        Optional[list[int]],
        None,
    ]

    InitSpecialEpisodeHero: Symbol[
        Optional[list[int]],
        None,
    ]

    EventFlagBackupVeneer: Symbol[
        Optional[list[int]],
        None,
    ]

    InitMainTeamAfterQuiz: Symbol[
        Optional[list[int]],
        None,
    ]

    InitSpecialEpisodePartners: Symbol[
        Optional[list[int]],
        None,
    ]

    InitSpecialEpisodeExtraPartner: Symbol[
        Optional[list[int]],
        None,
    ]

    ReadStringSave: Symbol[
        Optional[list[int]],
        None,
    ]

    CheckStringSave: Symbol[
        Optional[list[int]],
        None,
    ]

    WriteSaveFile: Symbol[
        Optional[list[int]],
        None,
    ]

    ReadSaveFile: Symbol[
        Optional[list[int]],
        None,
    ]

    CalcChecksum: Symbol[
        Optional[list[int]],
        None,
    ]

    CheckChecksumInvalid: Symbol[
        Optional[list[int]],
        None,
    ]

    NoteSaveBase: Symbol[
        Optional[list[int]],
        None,
    ]

    WriteQuickSaveInfo: Symbol[
        Optional[list[int]],
        None,
    ]

    ReadSaveHeader: Symbol[
        Optional[list[int]],
        None,
    ]

    NoteLoadBase: Symbol[
        Optional[list[int]],
        None,
    ]

    ReadQuickSaveInfo: Symbol[
        Optional[list[int]],
        None,
    ]

    GetGameMode: Symbol[
        Optional[list[int]],
        None,
    ]

    InitScriptVariableValues: Symbol[
        Optional[list[int]],
        None,
    ]

    InitEventFlagScriptVars: Symbol[
        Optional[list[int]],
        None,
    ]

    ZinitScriptVariable: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadScriptVariableRaw: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadScriptVariableValue: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadScriptVariableValueAtIndex: Symbol[
        Optional[list[int]],
        None,
    ]

    SaveScriptVariableValue: Symbol[
        Optional[list[int]],
        None,
    ]

    SaveScriptVariableValueAtIndex: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadScriptVariableValueSum: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadScriptVariableValueBytes: Symbol[
        Optional[list[int]],
        None,
    ]

    SaveScriptVariableValueBytes: Symbol[
        Optional[list[int]],
        None,
    ]

    ScriptVariablesEqual: Symbol[
        Optional[list[int]],
        None,
    ]

    EventFlagResume: Symbol[
        Optional[list[int]],
        None,
    ]

    EventFlagBackup: Symbol[
        Optional[list[int]],
        None,
    ]

    DumpScriptVariableValues: Symbol[
        Optional[list[int]],
        None,
    ]

    RestoreScriptVariableValues: Symbol[
        Optional[list[int]],
        None,
    ]

    InitScenarioScriptVars: Symbol[
        Optional[list[int]],
        None,
    ]

    SetScenarioScriptVar: Symbol[
        Optional[list[int]],
        None,
    ]

    GetSpecialEpisodeType: Symbol[
        Optional[list[int]],
        None,
    ]

    SetSpecialEpisodeType: Symbol[
        Optional[list[int]],
        None,
    ]

    GetExecuteSpecialEpisodeType: Symbol[
        Optional[list[int]],
        None,
    ]

    IsSpecialEpisodeOpen: Symbol[
        Optional[list[int]],
        None,
    ]

    HasPlayedOldGame: Symbol[
        Optional[list[int]],
        None,
    ]

    GetPerformanceFlagWithChecks: Symbol[
        Optional[list[int]],
        None,
    ]

    GetScenarioBalance: Symbol[
        Optional[list[int]],
        None,
    ]

    ScenarioFlagBackup: Symbol[
        Optional[list[int]],
        None,
    ]

    InitWorldMapScriptVars: Symbol[
        Optional[list[int]],
        None,
    ]

    InitDungeonListScriptVars: Symbol[
        Optional[list[int]],
        None,
    ]

    SetDungeonConquest: Symbol[
        Optional[list[int]],
        None,
    ]

    GetDungeonMode: Symbol[
        Optional[list[int]],
        None,
    ]

    GlobalProgressAlloc: Symbol[
        Optional[list[int]],
        None,
    ]

    ResetGlobalProgress: Symbol[
        Optional[list[int]],
        None,
    ]

    SetMonsterFlag1: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMonsterFlag1: Symbol[
        Optional[list[int]],
        None,
    ]

    SetMonsterFlag2: Symbol[
        Optional[list[int]],
        None,
    ]

    HasMonsterBeenAttackedInDungeons: Symbol[
        Optional[list[int]],
        None,
    ]

    SetDungeonTipShown: Symbol[
        Optional[list[int]],
        None,
    ]

    GetDungeonTipShown: Symbol[
        Optional[list[int]],
        None,
    ]

    SetMaxReachedFloor: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMaxReachedFloor: Symbol[
        Optional[list[int]],
        None,
    ]

    IncrementNbAdventures: Symbol[
        Optional[list[int]],
        None,
    ]

    GetNbAdventures: Symbol[
        Optional[list[int]],
        None,
    ]

    CanMonsterSpawn: Symbol[
        Optional[list[int]],
        None,
    ]

    IncrementExclusiveMonsterCounts: Symbol[
        Optional[list[int]],
        None,
    ]

    CopyProgressInfoTo: Symbol[
        Optional[list[int]],
        None,
    ]

    CopyProgressInfoFromScratchTo: Symbol[
        Optional[list[int]],
        None,
    ]

    CopyProgressInfoFrom: Symbol[
        Optional[list[int]],
        None,
    ]

    CopyProgressInfoFromScratchFrom: Symbol[
        Optional[list[int]],
        None,
    ]

    InitKaomadoStream: Symbol[
        Optional[list[int]],
        None,
    ]

    InitPortraitParams: Symbol[
        Optional[list[int]],
        None,
    ]

    InitPortraitParamsWithMonsterId: Symbol[
        Optional[list[int]],
        None,
    ]

    SetPortraitEmotion: Symbol[
        Optional[list[int]],
        None,
    ]

    SetPortraitLayout: Symbol[
        Optional[list[int]],
        None,
    ]

    SetPortraitOffset: Symbol[
        Optional[list[int]],
        None,
    ]

    AllowPortraitDefault: Symbol[
        Optional[list[int]],
        None,
    ]

    IsValidPortrait: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadPortrait: Symbol[
        Optional[list[int]],
        None,
    ]

    WonderMailPasswordToMission: Symbol[
        Optional[list[int]],
        None,
    ]

    SetEnterDungeon: Symbol[
        Optional[list[int]],
        None,
    ]

    InitDungeonInit: Symbol[
        Optional[list[int]],
        None,
    ]

    IsNoLossPenaltyDungeon: Symbol[
        Optional[list[int]],
        None,
    ]

    CheckMissionRestrictions: Symbol[
        Optional[list[int]],
        None,
    ]

    GetNbFloors: Symbol[
        Optional[list[int]],
        None,
    ]

    GetNbFloorsPlusOne: Symbol[
        Optional[list[int]],
        None,
    ]

    GetDungeonGroup: Symbol[
        Optional[list[int]],
        None,
    ]

    GetNbPrecedingFloors: Symbol[
        Optional[list[int]],
        None,
    ]

    GetNbFloorsDungeonGroup: Symbol[
        Optional[list[int]],
        None,
    ]

    DungeonFloorToGroupFloor: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMissionRank: Symbol[
        Optional[list[int]],
        None,
    ]

    GetOutlawLevel: Symbol[
        Optional[list[int]],
        None,
    ]

    GetOutlawLeaderLevel: Symbol[
        Optional[list[int]],
        None,
    ]

    GetOutlawMinionLevel: Symbol[
        Optional[list[int]],
        None,
    ]

    AddGuestMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    GetGroundNameId: Symbol[
        Optional[list[int]],
        None,
    ]

    SetAdventureLogStructLocation: Symbol[
        Optional[list[int]],
        None,
    ]

    SetAdventureLogDungeonFloor: Symbol[
        Optional[list[int]],
        None,
    ]

    GetAdventureLogDungeonFloor: Symbol[
        Optional[list[int]],
        None,
    ]

    ClearAdventureLogStruct: Symbol[
        Optional[list[int]],
        None,
    ]

    SetAdventureLogCompleted: Symbol[
        Optional[list[int]],
        None,
    ]

    IsAdventureLogNotEmpty: Symbol[
        Optional[list[int]],
        None,
    ]

    GetAdventureLogCompleted: Symbol[
        Optional[list[int]],
        None,
    ]

    IncrementNbDungeonsCleared: Symbol[
        Optional[list[int]],
        None,
    ]

    GetNbDungeonsCleared: Symbol[
        Optional[list[int]],
        None,
    ]

    IncrementNbFriendRescues: Symbol[
        Optional[list[int]],
        None,
    ]

    GetNbFriendRescues: Symbol[
        Optional[list[int]],
        None,
    ]

    IncrementNbEvolutions: Symbol[
        Optional[list[int]],
        None,
    ]

    GetNbEvolutions: Symbol[
        Optional[list[int]],
        None,
    ]

    IncrementNbSteals: Symbol[
        Optional[list[int]],
        None,
    ]

    IncrementNbEggsHatched: Symbol[
        Optional[list[int]],
        None,
    ]

    GetNbEggsHatched: Symbol[
        Optional[list[int]],
        None,
    ]

    GetNbPokemonJoined: Symbol[
        Optional[list[int]],
        None,
    ]

    GetNbMovesLearned: Symbol[
        Optional[list[int]],
        None,
    ]

    SetVictoriesOnOneFloor: Symbol[
        Optional[list[int]],
        None,
    ]

    GetVictoriesOnOneFloor: Symbol[
        Optional[list[int]],
        None,
    ]

    SetPokemonJoined: Symbol[
        Optional[list[int]],
        None,
    ]

    SetPokemonBattled: Symbol[
        Optional[list[int]],
        None,
    ]

    GetNbPokemonBattled: Symbol[
        Optional[list[int]],
        None,
    ]

    IncrementNbBigTreasureWins: Symbol[
        Optional[list[int]],
        None,
    ]

    SetNbBigTreasureWins: Symbol[
        Optional[list[int]],
        None,
    ]

    GetNbBigTreasureWins: Symbol[
        Optional[list[int]],
        None,
    ]

    SetNbRecycled: Symbol[
        Optional[list[int]],
        None,
    ]

    GetNbRecycled: Symbol[
        Optional[list[int]],
        None,
    ]

    IncrementNbSkyGiftsSent: Symbol[
        Optional[list[int]],
        None,
    ]

    SetNbSkyGiftsSent: Symbol[
        Optional[list[int]],
        None,
    ]

    GetNbSkyGiftsSent: Symbol[
        Optional[list[int]],
        None,
    ]

    ComputeSpecialCounters: Symbol[
        Optional[list[int]],
        None,
    ]

    RecruitSpecialPokemonLog: Symbol[
        Optional[list[int]],
        None,
    ]

    IncrementNbFainted: Symbol[
        Optional[list[int]],
        None,
    ]

    GetNbFainted: Symbol[
        Optional[list[int]],
        None,
    ]

    SetItemAcquired: Symbol[
        Optional[list[int]],
        None,
    ]

    GetNbItemAcquired: Symbol[
        Optional[list[int]],
        None,
    ]

    SetChallengeLetterCleared: Symbol[
        Optional[list[int]],
        None,
    ]

    GetSentryDutyGamePoints: Symbol[
        Optional[list[int]],
        None,
    ]

    SetSentryDutyGamePoints: Symbol[
        Optional[list[int]],
        None,
    ]

    CopyLogTo: Symbol[
        Optional[list[int]],
        None,
    ]

    CopyLogFrom: Symbol[
        Optional[list[int]],
        None,
    ]

    GetAbilityString: Symbol[
        Optional[list[int]],
        None,
    ]

    GetAbilityDescStringId: Symbol[
        Optional[list[int]],
        None,
    ]

    GetTypeStringId: Symbol[
        Optional[list[int]],
        None,
    ]

    GetConversion2ConvertToType: Symbol[
        Optional[list[int]],
        None,
    ]

    CopyBitsTo: Symbol[
        Optional[list[int]],
        None,
    ]

    CopyBitsFrom: Symbol[
        Optional[list[int]],
        None,
    ]

    StoreDefaultTeamData: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMainTeamNameWithCheck: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMainTeamName: Symbol[
        Optional[list[int]],
        None,
    ]

    SetMainTeamName: Symbol[
        Optional[list[int]],
        None,
    ]

    GetRankupPoints: Symbol[
        Optional[list[int]],
        None,
    ]

    GetRank: Symbol[
        Optional[list[int]],
        None,
    ]

    GetRankStorageSize: Symbol[
        Optional[list[int]],
        None,
    ]

    ResetPlayTimer: Symbol[
        Optional[list[int]],
        None,
    ]

    PlayTimerTick: Symbol[
        Optional[list[int]],
        None,
    ]

    GetPlayTimeSeconds: Symbol[
        Optional[list[int]],
        None,
    ]

    SubFixedPoint: Symbol[
        Optional[list[int]],
        None,
    ]

    BinToDecFixedPoint: Symbol[
        Optional[list[int]],
        None,
    ]

    CeilFixedPoint: Symbol[
        Optional[list[int]],
        None,
    ]

    DungeonGoesUp: Symbol[
        Optional[list[int]],
        None,
    ]

    GetTurnLimit: Symbol[
        Optional[list[int]],
        None,
    ]

    DoesNotSaveWhenEntering: Symbol[
        Optional[list[int]],
        None,
    ]

    TreasureBoxDropsEnabled: Symbol[
        Optional[list[int]],
        None,
    ]

    IsLevelResetDungeon: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMaxItemsAllowed: Symbol[
        Optional[list[int]],
        None,
    ]

    IsMoneyAllowed: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMaxRescueAttempts: Symbol[
        Optional[list[int]],
        None,
    ]

    IsRecruitingAllowed: Symbol[
        Optional[list[int]],
        None,
    ]

    GetLeaderChangeFlag: Symbol[
        Optional[list[int]],
        None,
    ]

    GetRandomMovementChance: Symbol[
        Optional[list[int]],
        None,
    ]

    CanEnemyEvolve: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMaxMembersAllowed: Symbol[
        Optional[list[int]],
        None,
    ]

    IsIqEnabled: Symbol[
        Optional[list[int]],
        None,
    ]

    IsTrapInvisibleWhenAttacking: Symbol[
        Optional[list[int]],
        None,
    ]

    JoinedAtRangeCheck: Symbol[
        Optional[list[int]],
        None,
    ]

    IsDojoDungeon: Symbol[
        Optional[list[int]],
        None,
    ]

    IsFutureDungeon: Symbol[
        Optional[list[int]],
        None,
    ]

    IsSpecialEpisodeDungeon: Symbol[
        Optional[list[int]],
        None,
    ]

    RetrieveFromItemList1: Symbol[
        Optional[list[int]],
        None,
    ]

    IsForbiddenFloor: Symbol[
        Optional[list[int]],
        None,
    ]

    Copy16BitsFrom: Symbol[
        Optional[list[int]],
        None,
    ]

    RetrieveFromItemList2: Symbol[
        Optional[list[int]],
        None,
    ]

    IsInvalidForMission: Symbol[
        Optional[list[int]],
        None,
    ]

    IsExpEnabledInDungeon: Symbol[
        Optional[list[int]],
        None,
    ]

    IsSkyExclusiveDungeon: Symbol[
        Optional[list[int]],
        None,
    ]

    JoinedAtRangeCheck2: Symbol[
        Optional[list[int]],
        None,
    ]

    GetBagCapacity: Symbol[
        Optional[list[int]],
        None,
    ]

    GetBagCapacitySpecialEpisode: Symbol[
        Optional[list[int]],
        None,
    ]

    GetRankUpEntry: Symbol[
        Optional[list[int]],
        None,
    ]

    GetBgRegionArea: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadMonsterMd: Symbol[
        Optional[list[int]],
        None,
    ]

    GetNameRaw: Symbol[
        Optional[list[int]],
        None,
    ]

    GetName: Symbol[
        Optional[list[int]],
        None,
    ]

    GetNameWithGender: Symbol[
        Optional[list[int]],
        None,
    ]

    GetSpeciesString: Symbol[
        Optional[list[int]],
        None,
    ]

    GetNameString: Symbol[
        Optional[list[int]],
        None,
    ]

    GetSpriteIndex: Symbol[
        Optional[list[int]],
        None,
    ]

    GetDexNumber: Symbol[
        Optional[list[int]],
        None,
    ]

    GetCategoryString: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMonsterGender: Symbol[
        Optional[list[int]],
        None,
    ]

    GetBodySize: Symbol[
        Optional[list[int]],
        None,
    ]

    GetSpriteSize: Symbol[
        Optional[list[int]],
        None,
    ]

    GetSpriteFileSize: Symbol[
        Optional[list[int]],
        None,
    ]

    GetShadowSize: Symbol[
        Optional[list[int]],
        None,
    ]

    GetSpeedStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMobilityType: Symbol[
        Optional[list[int]],
        None,
    ]

    GetRegenSpeed: Symbol[
        Optional[list[int]],
        None,
    ]

    GetCanMoveFlag: Symbol[
        Optional[list[int]],
        None,
    ]

    GetChanceAsleep: Symbol[
        Optional[list[int]],
        None,
    ]

    GetWeightMultiplier: Symbol[
        Optional[list[int]],
        None,
    ]

    GetSize: Symbol[
        Optional[list[int]],
        None,
    ]

    GetBaseHp: Symbol[
        Optional[list[int]],
        None,
    ]

    CanThrowItems: Symbol[
        Optional[list[int]],
        None,
    ]

    CanEvolve: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMonsterPreEvolution: Symbol[
        Optional[list[int]],
        None,
    ]

    GetBaseOffensiveStat: Symbol[
        Optional[list[int]],
        None,
    ]

    GetBaseDefensiveStat: Symbol[
        Optional[list[int]],
        None,
    ]

    GetType: Symbol[
        Optional[list[int]],
        None,
    ]

    GetAbility: Symbol[
        Optional[list[int]],
        None,
    ]

    GetRecruitRate2: Symbol[
        Optional[list[int]],
        None,
    ]

    GetRecruitRate1: Symbol[
        Optional[list[int]],
        None,
    ]

    GetExp: Symbol[
        Optional[list[int]],
        None,
    ]

    GetEvoParameters: Symbol[
        Optional[list[int]],
        None,
    ]

    GetTreasureBoxChances: Symbol[
        Optional[list[int]],
        None,
    ]

    GetIqGroup: Symbol[
        Optional[list[int]],
        None,
    ]

    GetSpawnThreshold: Symbol[
        Optional[list[int]],
        None,
    ]

    NeedsItemToSpawn: Symbol[
        Optional[list[int]],
        None,
    ]

    GetExclusiveItem: Symbol[
        Optional[list[int]],
        None,
    ]

    GetFamilyIndex: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadM2nAndN2m: Symbol[
        Optional[list[int]],
        None,
    ]

    GuestMonsterToGroundMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    StrcmpMonsterName: Symbol[
        Optional[list[int]],
        None,
    ]

    GetLvlUpEntry: Symbol[
        Optional[list[int]],
        None,
    ]

    GetEncodedHalfword: Symbol[
        Optional[list[int]],
        None,
    ]

    GetEvoFamily: Symbol[
        Optional[list[int]],
        None,
    ]

    GetEvolutions: Symbol[
        Optional[list[int]],
        None,
    ]

    ShuffleHiddenPower: Symbol[
        Optional[list[int]],
        None,
    ]

    GetBaseForm: Symbol[
        Optional[list[int]],
        None,
    ]

    GetBaseFormBurmyWormadamShellosGastrodonCherrim: Symbol[
        Optional[list[int]],
        None,
    ]

    GetBaseFormCastformCherrimDeoxys: Symbol[
        Optional[list[int]],
        None,
    ]

    GetAllBaseForms: Symbol[
        Optional[list[int]],
        None,
    ]

    GetDexNumberVeneer: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMonsterIdFromSpawnEntry: Symbol[
        Optional[list[int]],
        None,
    ]

    SetMonsterId: Symbol[
        Optional[list[int]],
        None,
    ]

    SetMonsterLevelAndId: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMonsterLevelFromSpawnEntry: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMonsterGenderVeneer: Symbol[
        Optional[list[int]],
        None,
    ]

    IsMonsterValid: Symbol[
        Optional[list[int]],
        None,
    ]

    IsUnown: Symbol[
        Optional[list[int]],
        None,
    ]

    IsShaymin: Symbol[
        Optional[list[int]],
        None,
    ]

    IsCastform: Symbol[
        Optional[list[int]],
        None,
    ]

    IsCherrim: Symbol[
        Optional[list[int]],
        None,
    ]

    IsDeoxys: Symbol[
        Optional[list[int]],
        None,
    ]

    GetSecondFormIfValid: Symbol[
        Optional[list[int]],
        None,
    ]

    FemaleToMaleForm: Symbol[
        Optional[list[int]],
        None,
    ]

    GetBaseFormCastformDeoxysCherrim: Symbol[
        Optional[list[int]],
        None,
    ]

    BaseFormsEqual: Symbol[
        Optional[list[int]],
        None,
    ]

    DexNumbersEqual: Symbol[
        Optional[list[int]],
        None,
    ]

    GendersEqual: Symbol[
        Optional[list[int]],
        None,
    ]

    GendersEqualNotGenderless: Symbol[
        Optional[list[int]],
        None,
    ]

    GendersNotEqualNotGenderless: Symbol[
        Optional[list[int]],
        None,
    ]

    IsMonsterOnTeam: Symbol[
        Optional[list[int]],
        None,
    ]

    GetNbRecruited: Symbol[
        Optional[list[int]],
        None,
    ]

    IsValidTeamMember: Symbol[
        Optional[list[int]],
        None,
    ]

    IsMainCharacter: Symbol[
        Optional[list[int]],
        None,
    ]

    GetTeamMember: Symbol[
        Optional[list[int]],
        None,
    ]

    GetHeroMemberIdx: Symbol[
        Optional[list[int]],
        None,
    ]

    GetPartnerMemberIdx: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMainCharacter1MemberIdx: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMainCharacter2MemberIdx: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMainCharacter3MemberIdx: Symbol[
        Optional[list[int]],
        None,
    ]

    GetHero: Symbol[
        Optional[list[int]],
        None,
    ]

    GetPartner: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMainCharacter1: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMainCharacter2: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMainCharacter3: Symbol[
        Optional[list[int]],
        None,
    ]

    GetFirstMatchingMemberIdx: Symbol[
        Optional[list[int]],
        None,
    ]

    GetFirstEmptyMemberIdx: Symbol[
        Optional[list[int]],
        None,
    ]

    IsMonsterNotNicknamed: Symbol[
        Optional[list[int]],
        None,
    ]

    RemoveActiveMembersFromAllTeams: Symbol[
        Optional[list[int]],
        None,
    ]

    RemoveActiveMembersFromSpecialEpisodeTeam: Symbol[
        Optional[list[int]],
        None,
    ]

    RemoveActiveMembersFromRescueTeam: Symbol[
        Optional[list[int]],
        None,
    ]

    CheckTeamMemberIdx: Symbol[
        Optional[list[int]],
        None,
    ]

    IsMonsterIdInNormalRange: Symbol[
        Optional[list[int]],
        None,
    ]

    SetActiveTeam: Symbol[
        Optional[list[int]],
        None,
    ]

    GetActiveTeamMember: Symbol[
        Optional[list[int]],
        None,
    ]

    GetActiveRosterIndex: Symbol[
        Optional[list[int]],
        None,
    ]

    TryAddMonsterToActiveTeam: Symbol[
        Optional[list[int]],
        None,
    ]

    RemoveActiveMembersFromMainTeam: Symbol[
        Optional[list[int]],
        None,
    ]

    SetTeamSetupHeroAndPartnerOnly: Symbol[
        Optional[list[int]],
        None,
    ]

    SetTeamSetupHeroOnly: Symbol[
        Optional[list[int]],
        None,
    ]

    GetPartyMembers: Symbol[
        Optional[list[int]],
        None,
    ]

    RefillTeam: Symbol[
        Optional[list[int]],
        None,
    ]

    ClearItem: Symbol[
        Optional[list[int]],
        None,
    ]

    ChangeGiratinaFormIfSkyDungeon: Symbol[
        Optional[list[int]],
        None,
    ]

    GetIqSkillStringId: Symbol[
        Optional[list[int]],
        None,
    ]

    DoesTacticFollowLeader: Symbol[
        Optional[list[int]],
        None,
    ]

    GetUnlockedTactics: Symbol[
        Optional[list[int]],
        None,
    ]

    GetUnlockedTacticFlags: Symbol[
        Optional[list[int]],
        None,
    ]

    CanLearnIqSkill: Symbol[
        Optional[list[int]],
        None,
    ]

    GetLearnableIqSkills: Symbol[
        Optional[list[int]],
        None,
    ]

    DisableIqSkill: Symbol[
        Optional[list[int]],
        None,
    ]

    EnableIqSkill: Symbol[
        Optional[list[int]],
        None,
    ]

    GetSpeciesIqSkill: Symbol[
        Optional[list[int]],
        None,
    ]

    DisableAllIqSkills: Symbol[
        Optional[list[int]],
        None,
    ]

    EnableAllLearnableIqSkills: Symbol[
        Optional[list[int]],
        None,
    ]

    IqSkillFlagTest: Symbol[
        Optional[list[int]],
        None,
    ]

    GetNextIqSkill: Symbol[
        Optional[list[int]],
        None,
    ]

    GetExplorerMazeTeamName: Symbol[
        Optional[list[int]],
        None,
    ]

    GetExplorerMazeMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    WriteMonsterInfoToSave: Symbol[
        Optional[list[int]],
        None,
    ]

    ReadMonsterInfoFromSave: Symbol[
        Optional[list[int]],
        None,
    ]

    WriteMonsterToSave: Symbol[
        Optional[list[int]],
        None,
    ]

    ReadMonsterFromSave: Symbol[
        Optional[list[int]],
        None,
    ]

    GetEvolutionPossibilities: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMonsterEvoStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    CopyTacticString: Symbol[
        Optional[list[int]],
        None,
    ]

    GetStatBoostsForMonsterSummary: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateMonsterSummaryFromTeamMember: Symbol[
        Optional[list[int]],
        None,
    ]

    GetSosMailCount: Symbol[
        Optional[list[int]],
        None,
    ]

    IsMissionSuspendedAndValid: Symbol[
        Optional[list[int]],
        None,
    ]

    AreMissionsEquivalent: Symbol[
        Optional[list[int]],
        None,
    ]

    IsMissionValid: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateMission: Symbol[
        Optional[list[int]],
        None,
    ]

    IsMissionTypeSpecialEpisode: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateDailyMissions: Symbol[
        Optional[list[int]],
        None,
    ]

    AlreadyHaveMission: Symbol[
        Optional[list[int]],
        None,
    ]

    CountJobListMissions: Symbol[
        Optional[list[int]],
        None,
    ]

    DungeonRequestsDone: Symbol[
        Optional[list[int]],
        None,
    ]

    DungeonRequestsDoneWrapper: Symbol[
        Optional[list[int]],
        None,
    ]

    AnyDungeonRequestsDone: Symbol[
        Optional[list[int]],
        None,
    ]

    AddMissionToJobList: Symbol[
        Optional[list[int]],
        None,
    ]

    GetAcceptedMission: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMissionByTypeAndDungeon: Symbol[
        Optional[list[int]],
        None,
    ]

    CheckAcceptedMissionByTypeAndDungeon: Symbol[
        Optional[list[int]],
        None,
    ]

    GetAllPossibleMonsters: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateAllPossibleMonstersList: Symbol[
        Optional[list[int]],
        None,
    ]

    DeleteAllPossibleMonstersList: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateAllPossibleDungeonsList: Symbol[
        Optional[list[int]],
        None,
    ]

    DeleteAllPossibleDungeonsList: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateAllPossibleDeliverList: Symbol[
        Optional[list[int]],
        None,
    ]

    DeleteAllPossibleDeliverList: Symbol[
        Optional[list[int]],
        None,
    ]

    ClearMissionData: Symbol[
        Optional[list[int]],
        None,
    ]

    IsMonsterMissionAllowed: Symbol[
        Optional[list[int]],
        None,
    ]

    CanMonsterBeUsedForMissionWrapper: Symbol[
        Optional[list[int]],
        None,
    ]

    CanMonsterBeUsedForMission: Symbol[
        Optional[list[int]],
        None,
    ]

    IsMonsterMissionAllowedStory: Symbol[
        Optional[list[int]],
        None,
    ]

    CanDungeonBeUsedForMission: Symbol[
        Optional[list[int]],
        None,
    ]

    CanSendItem: Symbol[
        Optional[list[int]],
        None,
    ]

    IsAvailableItem: Symbol[
        Optional[list[int]],
        None,
    ]

    GetAvailableItemDeliveryList: Symbol[
        Optional[list[int]],
        None,
    ]

    GetActorMatchingStorageId: Symbol[
        Optional[list[int]],
        None,
    ]

    SetActorTalkMainAndActorTalkSub: Symbol[
        Optional[list[int]],
        None,
    ]

    SetActorTalkMain: Symbol[
        Optional[list[int]],
        None,
    ]

    SetActorTalkSub: Symbol[
        Optional[list[int]],
        None,
    ]

    RandomizeDemoActors: Symbol[
        Optional[list[int]],
        None,
    ]

    ItemAtTableIdx: Symbol[
        Optional[list[int]],
        None,
    ]

    MainLoop: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateJobSummary: Symbol[
        Optional[list[int]],
        None,
    ]

    DungeonSwapIdToIdx: Symbol[
        Optional[list[int]],
        None,
    ]

    DungeonSwapIdxToId: Symbol[
        Optional[list[int]],
        None,
    ]

    GetDungeonModeSpecial: Symbol[
        Optional[list[int]],
        None,
    ]


class Arm9DataProtocol(Protocol):

    SECURE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    START_MODULE_PARAMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DEFAULT_MEMORY_ARENA_SIZE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LOG_MAX_ARG: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DAMAGE_SOURCE_CODE_ORB_ITEM: Symbol[
        Optional[list[int]],
        None,
    ]

    DAMAGE_SOURCE_CODE_NON_ORB_ITEM: Symbol[
        Optional[list[int]],
        None,
    ]

    AURA_BOW_ID_LAST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    NUMBER_OF_ITEMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MAX_MONEY_CARRIED: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MAX_MONEY_STORED: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    WINDOW_LIST_PTR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SCRIPT_VARS_VALUES_PTR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MAX_PLAY_TIME: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MONSTER_ID_LIMIT: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MAX_RECRUITABLE_TEAM_MEMBERS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    NATURAL_LOG_VALUE_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    CART_REMOVED_IMG_DATA: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_DEBUG_EMPTY: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_DEBUG_FORMAT_LINE_FILE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_DEBUG_NO_PROG_POS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_DEBUG_SPACED_PRINT: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_DEBUG_FATAL: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_DEBUG_NEWLINE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_DEBUG_LOG_NULL: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_DEBUG_STRING_NEWLINE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_EFFECT_EFFECT_BIN: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_MONSTER_MONSTER_BIN: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_BALANCE_M_LEVEL_BIN: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_DUNGEON_DUNGEON_BIN: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_MONSTER_M_ATTACK_BIN: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_MONSTER_M_GROUND_BIN: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_FILE_DIRECTORY_INIT: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    AVAILABLE_ITEMS_IN_GROUP_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ARM9_UNKNOWN_TABLE__NA_2097FF8: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    KECLEON_SHOP_ITEM_TABLE_LISTS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    KECLEON_SHOP_ITEM_TABLE_LISTS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EXCLUSIVE_ITEM_STAT_BOOST_DATA: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EXCLUSIVE_ITEM_DEFENSE_BOOSTS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EXCLUSIVE_ITEM_SPECIAL_ATTACK_BOOSTS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EXCLUSIVE_ITEM_SPECIAL_DEFENSE_BOOSTS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EXCLUSIVE_ITEM_EFFECT_DATA: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EXCLUSIVE_ITEM_STAT_BOOST_DATA_INDEXES: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RECYCLE_SHOP_ITEM_LIST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TYPE_SPECIFIC_EXCLUSIVE_ITEMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RECOIL_MOVE_LIST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    PUNCH_MOVE_LIST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MOVE_POWER_STARS_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MOVE_ACCURACY_STARS_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    PARENT_MENU_DEFAULT_WINDOW_PARAMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SIMPLE_MENU_DEFAULT_WINDOW_PARAMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ADVANCED_MENU_DEFAULT_WINDOW_PARAMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    COLLECTION_MENU_DEFAULT_WINDOW_PARAMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OPTIONS_MENU_DEFAULT_WINDOW_PARAMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DEBUG_MENU_DEFAULT_WINDOW_PARAMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SCROLL_BOX_DEFAULT_WINDOW_PARAMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DIALOGUE_BOX_DEFAULT_WINDOW_PARAMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    PORTRAIT_BOX_DEFAULT_WINDOW_PARAMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TEXT_BOX_DEFAULT_WINDOW_PARAMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    AREA_NAME_BOX_DEFAULT_WINDOW_PARAMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    CONTROLS_CHART_DEFAULT_WINDOW_PARAMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ALERT_BOX_DEFAULT_WINDOW_PARAMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ADVANCED_TEXT_BOX_DEFAULT_WINDOW_PARAMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TEAM_SELECTION_MENU_DEFAULT_WINDOW_PARAMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    PARTNER_TALK_KIND_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SCRIPT_VARS_LOCALS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SCRIPT_VARS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    PORTRAIT_LAYOUTS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    KAOMADO_FILEPATH: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    WONDER_MAIL_BITS_MAP: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    WONDER_MAIL_BITS_SWAP: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ARM9_UNKNOWN_TABLE__NA_209E12C: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ARM9_UNKNOWN_TABLE__NA_209E164: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ARM9_UNKNOWN_TABLE__NA_209E280: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    WONDER_MAIL_ENCRYPTION_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_DATA_LIST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ADVENTURE_LOG_ENCOUNTERS_MONSTER_IDS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ARM9_UNKNOWN_DATA__NA_209E6BC: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TACTIC_NAME_STRING_IDS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STATUS_NAME_STRING_IDS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_RETURN_STATUS_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STATUSES_FULL_DESCRIPTION_STRING_IDS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ARM9_UNKNOWN_DATA__NA_209EAAC: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MISSION_FLOOR_RANKS_AND_ITEM_LISTS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MISSION_FLOORS_FORBIDDEN: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MISSION_FLOOR_RANKS_AND_ITEM_LISTS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MISSION_FLOOR_RANKS_PTRS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_RESTRICTIONS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SPECIAL_BAND_STAT_BOOST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MUNCH_BELT_STAT_BOOST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    GUMMI_STAT_BOOST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MIN_IQ_EXCLUSIVE_MOVE_USER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    WONDER_GUMMI_IQ_GAIN: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    AURA_BOW_STAT_BOOST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MIN_IQ_ITEM_MASTER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DEF_SCARF_STAT_BOOST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    POWER_BAND_STAT_BOOST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    WONDER_GUMMI_STAT_BOOST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ZINC_BAND_STAT_BOOST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EGG_HP_BONUS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EVOLUTION_HP_BONUS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DAMAGE_FORMULA_FLV_SHIFT: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EVOLUTION_PHYSICAL_STAT_BONUSES: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DAMAGE_FORMULA_CONSTANT_SHIFT: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DAMAGE_FORMULA_FLV_DEFICIT_DIVISOR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EGG_STAT_BONUSES: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EVOLUTION_SPECIAL_STAT_BONUSES: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DAMAGE_FORMULA_NON_TEAM_MEMBER_MODIFIER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DAMAGE_FORMULA_LN_PREFACTOR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DAMAGE_FORMULA_DEF_PREFACTOR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DAMAGE_FORMULA_AT_PREFACTOR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DAMAGE_FORMULA_LN_ARG_PREFACTOR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    FORBIDDEN_FORGOT_MOVE_LIST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TACTICS_UNLOCK_LEVEL_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    CLIENT_LEVEL_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OUTLAW_LEVEL_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OUTLAW_MINION_LEVEL_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    HIDDEN_POWER_BASE_POWER_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    VERSION_EXCLUSIVE_MONSTERS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    IQ_SKILL_RESTRICTIONS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SECONDARY_TERRAIN_TYPES: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SENTRY_DUTY_MONSTER_IDS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    IQ_SKILLS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    IQ_GROUP_SKILLS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MONEY_QUANTITY_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ARM9_UNKNOWN_TABLE__NA_20A20B0: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    IQ_GUMMI_GAIN_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    GUMMI_BELLY_RESTORE_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BAG_CAPACITY_TABLE_SPECIAL_EPISODES: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BAG_CAPACITY_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SPECIAL_EPISODE_MAIN_CHARACTERS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    GUEST_MONSTER_DATA: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RANK_UP_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DS_DOWNLOAD_TEAMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ARM9_UNKNOWN_PTR__NA_20A2C84: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    UNOWN_SPECIES_ADDITIONAL_CHARS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MONSTER_SPRITE_DATA: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    REMOTE_STRINGS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RANK_STRINGS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MISSION_MENU_STRING_IDS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RANK_STRINGS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MISSION_MENU_STRING_IDS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RANK_STRINGS_3: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MISSION_DUNGEON_UNLOCK_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    NO_SEND_ITEM_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ARM9_UNKNOWN_TABLE__NA_20A3CC8: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ARM9_UNKNOWN_TABLE__NA_20A3CE4: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ARM9_UNKNOWN_FUNCTION_TABLE__NA_20A3CF4: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MISSION_BANNED_STORY_MONSTERS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ITEM_DELIVERY_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MISSION_RANK_POINTS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MISSION_BANNED_MONSTERS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MISSION_STRING_IDS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LEVEL_LIST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EVENTS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ARM9_UNKNOWN_TABLE__NA_20A68BC: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DEMO_TEAMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ACTOR_LIST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ENTITIES: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    JOB_WINDOW_PARAMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    JOB_MENU_ITEMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    JOB_MENU_ITEMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    JOB_MENU_ITEMS_3: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    JOB_MENU_ITEMS_4: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    JOB_MENU_ITEMS_5: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    JOB_MENU_ITEMS_6: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    JOB_MENU_ITEMS_7: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    JOB_MENU_ITEMS_8: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    JOB_MENU_ITEMS_9: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    JOB_MENU_ITEMS_10: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    JOB_MENU_ITEMS_11: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    JOB_MENU_ITEMS_12: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    JOB_MENU_ITEMS_13: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    JOB_WINDOW_PARAMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_SWAP_ID_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MAP_MARKER_PLACEMENTS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LFO_OUTPUT_VOICE_UPDATE_FLAGS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TRIG_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    FX_ATAN_IDX_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TEX_PLTT_START_ADDR_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TEX_START_ADDR_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ARM9_UNKNOWN_TABLE__NA_20AE924: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MEMORY_ALLOCATION_ARENA_GETTERS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    PRNG_SEQUENCE_NUM: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LOADED_OVERLAY_GROUP_0: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LOADED_OVERLAY_GROUP_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LOADED_OVERLAY_GROUP_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DEBUG_IS_INITIALIZED: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    PACK_FILES_OPENED: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    PACK_FILE_PATHS_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    GAME_STATE_VALUES: Symbol[
        Optional[list[int]],
        None,
    ]

    BAG_ITEMS_PTR_MIRROR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ITEM_DATA_TABLE_PTRS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_MOVE_TABLES: Symbol[
        Optional[list[int]],
        None,
    ]

    MOVE_DATA_TABLE_PTR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    WAN_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RENDER_3D: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RENDER_3D_FUNCTIONS_64: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LANGUAGE_INFO_DATA: Symbol[
        Optional[list[int]],
        None,
    ]

    TBL_TALK_GROUP_STRING_ID_START: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    KEYBOARD_STRING_IDS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    NOTIFY_NOTE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DEFAULT_HERO_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DEFAULT_PARTNER_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    GAME_MODE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    GLOBAL_PROGRESS_PTR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ADVENTURE_LOG_PTR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ITEM_TABLES_PTRS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    UNOWN_SPECIES_ADDITIONAL_CHAR_PTR_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TEAM_MEMBER_TABLE_PTR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MISSION_DELIVER_LIST_PTR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MISSION_DELIVER_COUNT: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MISSION_DUNGEON_LIST_PTR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MISSION_DUNGEON_COUNT: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MISSION_MONSTER_LIST_PTR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MISSION_MONSTER_COUNT: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MISSION_LIST_PTR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    REMOTE_STRING_PTR_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RANK_STRING_PTR_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SMD_EVENTS_FUN_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MUSIC_DURATION_LOOKUP_TABLE_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MUSIC_DURATION_LOOKUP_TABLE_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LFO_WAVEFORM_CALLBACKS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    IS_DISP_ON: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    GXI_DMA_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    JUICE_BAR_NECTAR_IQ_GAIN: Symbol[
        Optional[list[int]],
        None,
    ]

    DEBUG_TEXT_SPEED: Symbol[
        Optional[list[int]],
        None,
    ]

    REGULAR_TEXT_SPEED: Symbol[
        Optional[list[int]],
        None,
    ]

    HERO_START_LEVEL: Symbol[
        Optional[list[int]],
        None,
    ]

    PARTNER_START_LEVEL: Symbol[
        Optional[list[int]],
        None,
    ]


Arm9Protocol = SectionProtocol[
    Arm9FunctionsProtocol,
    Arm9DataProtocol,
    int,
]


class ItcmFunctionsProtocol(Protocol):

    CopyAndInterleave: Symbol[
        list[int],
        None,
    ]

    Render3dSetTextureParams: Symbol[
        list[int],
        None,
    ]

    Render3dSetPaletteBase: Symbol[
        list[int],
        None,
    ]

    Render3dRectangle: Symbol[
        list[int],
        None,
    ]

    GeomSetPolygonAttributes: Symbol[
        list[int],
        None,
    ]

    Render3dQuadrilateral: Symbol[
        list[int],
        None,
    ]

    Render3dTiling: Symbol[
        list[int],
        None,
    ]

    Render3dTextureInternal: Symbol[
        list[int],
        None,
    ]

    Render3dTexture: Symbol[
        list[int],
        None,
    ]

    Render3dTextureNoSetup: Symbol[
        list[int],
        None,
    ]

    NewRender3dElement: Symbol[
        list[int],
        None,
    ]

    EnqueueRender3dTexture: Symbol[
        list[int],
        None,
    ]

    EnqueueRender3dTiling: Symbol[
        list[int],
        None,
    ]

    NewRender3dRectangle: Symbol[
        list[int],
        None,
    ]

    NewRender3dQuadrilateral: Symbol[
        list[int],
        None,
    ]

    NewRender3dTexture: Symbol[
        list[int],
        None,
    ]

    NewRender3dTiling: Symbol[
        list[int],
        None,
    ]

    Render3dProcessQueue: Symbol[
        list[int],
        None,
    ]

    GetKeyN2MSwitch: Symbol[
        list[int],
        None,
    ]

    GetKeyN2M: Symbol[
        list[int],
        None,
    ]

    GetKeyN2MBaseForm: Symbol[
        list[int],
        None,
    ]

    GetKeyM2NSwitch: Symbol[
        list[int],
        None,
    ]

    GetKeyM2N: Symbol[
        list[int],
        None,
    ]

    GetKeyM2NBaseForm: Symbol[
        list[int],
        None,
    ]

    HardwareInterrupt: Symbol[
        list[int],
        None,
    ]

    ReturnFromInterrupt: Symbol[
        list[int],
        None,
    ]

    InitDmaTransfer_Standard: Symbol[
        list[int],
        None,
    ]

    ShouldMonsterRunAwayVariationOutlawCheck: Symbol[
        list[int],
        None,
    ]

    AiMovement: Symbol[
        list[int],
        None,
    ]

    CalculateAiTargetPos: Symbol[
        list[int],
        None,
    ]

    ChooseAiMove: Symbol[
        list[int],
        None,
    ]

    LightningRodStormDrainCheck: Symbol[
        list[int],
        None,
    ]


class ItcmDataProtocol(Protocol):

    MEMORY_ALLOCATION_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DEFAULT_MEMORY_ARENA: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DEFAULT_MEMORY_ARENA_BLOCKS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RENDER_3D_FUNCTIONS: Symbol[
        Optional[list[int]],
        None,
    ]


ItcmProtocol = SectionProtocol[
    ItcmFunctionsProtocol,
    ItcmDataProtocol,
    int,
]


class LibsFunctionsProtocol(Protocol):

    DseDriver_LoadDefaultSettings: Symbol[
        Optional[list[int]],
        None,
    ]

    DseDriver_IsSettingsValid: Symbol[
        Optional[list[int]],
        None,
    ]

    DseDriver_ConfigureHeap: Symbol[
        Optional[list[int]],
        None,
    ]

    DseDriver_Init: Symbol[
        Optional[list[int]],
        None,
    ]

    Dse_SetError: Symbol[
        Optional[list[int]],
        None,
    ]

    Dse_SetError2: Symbol[
        Optional[list[int]],
        None,
    ]

    DseUtil_ByteSwap32: Symbol[
        Optional[list[int]],
        None,
    ]

    SoundUtil_GetRandomNumber: Symbol[
        Optional[list[int]],
        None,
    ]

    DseMem_Init: Symbol[
        Optional[list[int]],
        None,
    ]

    DseMem_Quit: Symbol[
        Optional[list[int]],
        None,
    ]

    DseMem_AllocateUser: Symbol[
        Optional[list[int]],
        None,
    ]

    DseMem_Allocate: Symbol[
        Optional[list[int]],
        None,
    ]

    DseMem_AllocateThreadStack: Symbol[
        Optional[list[int]],
        None,
    ]

    DseMem_Free: Symbol[
        Optional[list[int]],
        None,
    ]

    DseMem_Clear: Symbol[
        Optional[list[int]],
        None,
    ]

    DseFile_CheckHeader: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSwd_SysInit: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSwd_SysQuit: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSwd_SampleLoaderMain: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSwd_MainBankDummyCallback: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSwd_LoadMainBank: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSwd_LoadBank: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSwd_IsBankLoading: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSwd_LoadWaves: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSwd_LoadWavesInternal: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSwd_Unload: Symbol[
        Optional[list[int]],
        None,
    ]

    ReadWaviEntry: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSwd_GetInstrument: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSwd_GetNextSplitInRange: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSwd_GetMainBankById: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSwd_GetBankById: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSwd_InitMainBankFileReader: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSwd_OpenMainBankFileReader: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSwd_CloseMainBankFileReader: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSwd_ReadMainBank: Symbol[
        Optional[list[int]],
        None,
    ]

    DseBgm_DefaultSignalCallback: Symbol[
        Optional[list[int]],
        None,
    ]

    DseBgm_Load: Symbol[
        Optional[list[int]],
        None,
    ]

    DseBgm_Unload: Symbol[
        Optional[list[int]],
        None,
    ]

    DseBgm_SetSignalCallback: Symbol[
        Optional[list[int]],
        None,
    ]

    DseBgm_IsPlaying: Symbol[
        Optional[list[int]],
        None,
    ]

    ResumeBgm: Symbol[
        Optional[list[int]],
        None,
    ]

    DseBgm_Stop: Symbol[
        Optional[list[int]],
        None,
    ]

    DseBgm_StopAll: Symbol[
        Optional[list[int]],
        None,
    ]

    DseBgm_SetFades: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSequence_Start: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSequence_PauseList: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSequence_SetFades: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSequence_GetParameter: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSequence_GetSmallestNumLoops: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSequence_Reset: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSequence_Stop: Symbol[
        Optional[list[int]],
        None,
    ]

    FindSmdlSongChunk: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSequence_LoadSong: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSequence_GetById: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSequence_AllocateNew: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSequence_Unload: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSequence_InitTracks: Symbol[
        Optional[list[int]],
        None,
    ]

    DseBgm_SysSetupNoteList: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSe_SysReset: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSe_Load: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSe_Unload: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSe_GetUsedBankIDs: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSe_HasPlayingInstances: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSe_Play: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSe_GetEffectSong: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSe_CheckTooManyInstances: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSe_CheckTooManyInstancesInGroup: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSe_GetBestSeqAllocation: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSe_GetById: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSe_Stop: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSe_StopAll: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSe_StopSeq: Symbol[
        Optional[list[int]],
        None,
    ]

    FlushChannels: Symbol[
        Optional[list[int]],
        None,
    ]

    DseDriver_StartMainThread: Symbol[
        Optional[list[int]],
        None,
    ]

    DseDriver_StartTickTimer: Symbol[
        Optional[list[int]],
        None,
    ]

    DseDriver_NotifyTick: Symbol[
        Optional[list[int]],
        None,
    ]

    DseDriver_Main: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSequence_TickNotes: Symbol[
        Optional[list[int]],
        None,
    ]

    ParseDseEvent: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateSequencerTracks: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSequence_TickFades: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_Invalid: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_WaitSame: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_WaitDelta: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_Wait8: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_Wait16: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_Wait24: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_WaitUntilFadeout: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_EndTrack: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_MainLoopBegin: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SubLoopBegin: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SubLoopEnd: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SubLoopBreakOnLastIteration: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetOctave: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_OctaveDelta: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetBpm: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetBpm2: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetBank: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetBankMsb: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetBankLsb: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_Dummy1Byte: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetInstrument: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SongVolumeFade: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_RestoreEnvelopeDefaults: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetEnvelopeAttackBegin: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetEnvelopeAttackTime: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetEnvelopeHoldTime: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetEnvelopeDecayTimeAndSustainLevel: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetEnvelopeSustainTime: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetEnvelopeReleaseTime: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetNoteDurationMultiplier: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_ForceLfoEnvelopeLevel: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetHoldNotes: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetFlagBit1Unknown: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetOptionalVolume: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_Dummy2Bytes: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetTuning: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_TuningDeltaCoarse: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_TuningDeltaFine: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_TuningDeltaFull: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_TuningFade: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetNoteRandomRegion: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetTuningJitterAmplitude: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetKeyBend: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetUnknown2: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetKeyBendRange: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetupKeyBendLfo: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetupKeyBendLfoEnvelope: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_UseKeyBendLfo: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetVolume: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_VolumeDelta: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_VolumeFade: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetExpression: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetupVolumeLfo: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetupVolumeLfoEnvelope: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_UseVolumeLfo: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetPan: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_PanDelta: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_PanFade: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetupPanLfo: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetupPanLfoEnvelope: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_UsePanLfo: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetupLfo: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetupLfoEnvelope: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_SetLfoParameter: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_UseLfo: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_Signal: Symbol[
        Optional[list[int]],
        None,
    ]

    DseTrackEvent_Dummy2Bytes2: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSynth_Reset: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSynth_AllocateNew: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSynth_Unload: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSynth_ClearHeldNotes: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSynth_ResetAndSetBankAndSequence: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSynth_StopChannels: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSynth_ResetAllVoiceTimersAndVolumes: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSynth_RestoreHeldNotes: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSynth_SetGlobalVolumeIndex: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSynth_SetBend: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSynth_SetVolume: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSynth_SetPan: Symbol[
        Optional[list[int]],
        None,
    ]

    DseSynth_SetBankAndSequence: Symbol[
        Optional[list[int]],
        None,
    ]

    DseChannel_Init: Symbol[
        Optional[list[int]],
        None,
    ]

    DseChannel_DeallocateVoices: Symbol[
        Optional[list[int]],
        None,
    ]

    DseChannel_ResetTimerAndVolumeForVoices: Symbol[
        Optional[list[int]],
        None,
    ]

    DseChannel_SetBank: Symbol[
        Optional[list[int]],
        None,
    ]

    DseChannel_SetInstrument: Symbol[
        Optional[list[int]],
        None,
    ]

    DseChannel_SetLfoConstEnvelopeLevel: Symbol[
        Optional[list[int]],
        None,
    ]

    DseChannel_SetKeyBend: Symbol[
        Optional[list[int]],
        None,
    ]

    DseChannel_AllocateNote: Symbol[
        Optional[list[int]],
        None,
    ]

    DseChannel_ReleaseNoteInternal: Symbol[
        Optional[list[int]],
        None,
    ]

    DseChannel_ChangeNote: Symbol[
        Optional[list[int]],
        None,
    ]

    DseChannel_ReleaseNote: Symbol[
        Optional[list[int]],
        None,
    ]

    DseVoice_PlayNote: Symbol[
        Optional[list[int]],
        None,
    ]

    DseVoice_ReleaseNote: Symbol[
        Optional[list[int]],
        None,
    ]

    DseVoice_UpdateParameters: Symbol[
        Optional[list[int]],
        None,
    ]

    DseVoice_ResetAll: Symbol[
        Optional[list[int]],
        None,
    ]

    DseVoice_ResetHW: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateChannels: Symbol[
        Optional[list[int]],
        None,
    ]

    DseVoice_Cleanup: Symbol[
        Optional[list[int]],
        None,
    ]

    DseVoice_Allocate: Symbol[
        Optional[list[int]],
        None,
    ]

    DseVoice_Start: Symbol[
        Optional[list[int]],
        None,
    ]

    DseVoice_ReleaseHeld: Symbol[
        Optional[list[int]],
        None,
    ]

    DseVoice_Release: Symbol[
        Optional[list[int]],
        None,
    ]

    DseVoice_Deallocate: Symbol[
        Optional[list[int]],
        None,
    ]

    DseVoice_FlagForActivation: Symbol[
        Optional[list[int]],
        None,
    ]

    DseVoice_FlagForDeactivation: Symbol[
        Optional[list[int]],
        None,
    ]

    DseVoice_CountNumActiveInChannel: Symbol[
        Optional[list[int]],
        None,
    ]

    DseVoice_UpdateHardware: Symbol[
        Optional[list[int]],
        None,
    ]

    SoundEnvelope_Reset: Symbol[
        Optional[list[int]],
        None,
    ]

    SoundEnvelopeParameters_Reset: Symbol[
        Optional[list[int]],
        None,
    ]

    SoundEnvelopeParameters_CheckValidity: Symbol[
        Optional[list[int]],
        None,
    ]

    SoundEnvelope_SetParameters: Symbol[
        Optional[list[int]],
        None,
    ]

    SoundEnvelope_SetSlide: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateTrackVolumeEnvelopes: Symbol[
        Optional[list[int]],
        None,
    ]

    SoundEnvelope_Release: Symbol[
        Optional[list[int]],
        None,
    ]

    SoundEnvelope_Stop: Symbol[
        Optional[list[int]],
        None,
    ]

    SoundEnvelope_ForceVolume: Symbol[
        Optional[list[int]],
        None,
    ]

    SoundEnvelope_Stop2: Symbol[
        Optional[list[int]],
        None,
    ]

    SoundEnvelope_Tick: Symbol[
        Optional[list[int]],
        None,
    ]

    SoundLfoBank_Reset: Symbol[
        Optional[list[int]],
        None,
    ]

    SoundLfoBank_Set: Symbol[
        Optional[list[int]],
        None,
    ]

    SoundLfoBank_SetConstEnvelopes: Symbol[
        Optional[list[int]],
        None,
    ]

    SoundLfoBank_Tick: Symbol[
        Optional[list[int]],
        None,
    ]

    SoundLfoWave_InvalidFunc: Symbol[
        Optional[list[int]],
        None,
    ]

    SoundLfoWave_HalfSquareFunc: Symbol[
        Optional[list[int]],
        None,
    ]

    SoundLfoWave_FullSquareFunc: Symbol[
        Optional[list[int]],
        None,
    ]

    SoundLfoWave_HalfTriangleFunc: Symbol[
        Optional[list[int]],
        None,
    ]

    SoundLfoWave_FullTriangleFunc: Symbol[
        Optional[list[int]],
        None,
    ]

    SoundLfoWave_SawFunc: Symbol[
        Optional[list[int]],
        None,
    ]

    SoundLfoWave_ReverseSawFunc: Symbol[
        Optional[list[int]],
        None,
    ]

    SoundLfoWave_HalfNoiseFunc: Symbol[
        Optional[list[int]],
        None,
    ]

    SoundLfoWave_FullNoiseFunc: Symbol[
        Optional[list[int]],
        None,
    ]

    Crypto_RC4Init: Symbol[
        Optional[list[int]],
        None,
    ]

    Mtx_LookAt: Symbol[
        Optional[list[int]],
        None,
    ]

    Mtx_OrthoW: Symbol[
        Optional[list[int]],
        None,
    ]

    FX_Div: Symbol[
        Optional[list[int]],
        None,
    ]

    FX_GetDivResultFx64c: Symbol[
        Optional[list[int]],
        None,
    ]

    FX_GetDivResult: Symbol[
        Optional[list[int]],
        None,
    ]

    FX_InvAsync: Symbol[
        Optional[list[int]],
        None,
    ]

    FX_DivAsync: Symbol[
        Optional[list[int]],
        None,
    ]

    FX_DivS32: Symbol[
        Optional[list[int]],
        None,
    ]

    FX_ModS32: Symbol[
        Optional[list[int]],
        None,
    ]

    Vec_DotProduct: Symbol[
        Optional[list[int]],
        None,
    ]

    Vec_CrossProduct: Symbol[
        Optional[list[int]],
        None,
    ]

    Vec_Normalize: Symbol[
        Optional[list[int]],
        None,
    ]

    Vec_Distance: Symbol[
        Optional[list[int]],
        None,
    ]

    FX_Atan2Idx: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_Init: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_HBlankIntr: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_VBlankIntr: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_DispOff: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_DispOn: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_SetGraphicsMode: Symbol[
        Optional[list[int]],
        None,
    ]

    Gxs_SetGraphicsMode: Symbol[
        Optional[list[int]],
        None,
    ]

    GXx_SetMasterBrightness: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_InitGxState: Symbol[
        Optional[list[int]],
        None,
    ]

    EnableVramBanksInSetDontSave: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_SetBankForBg: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_SetBankForObj: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_SetBankForBgExtPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_SetBankForObjExtPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_SetBankForTex: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_SetBankForTexPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_SetBankForClearImage: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_SetBankForArm7: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_SetBankForLcdc: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_SetBankForSubBg: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_SetBankForSubObj: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_SetBankForSubBgExtPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_SetBankForSubObjExtPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    EnableVramBanksInSet: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_ResetBankForBgExtPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_ResetBankForObjExtPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_ResetBankForTex: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_ResetBankForTexPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_ResetBankForSubBgExtPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_ResetBankForSubObjExtPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    DisableBankForX: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_DisableBankForBg: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_DisableBankForObj: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_DisableBankForBgExtPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_DisableBankForObjExtPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_DisableBankForTex: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_DisableBankForTexPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_DisableBankForClearImage: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_DisableBankForArm7: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_DisableBankForLcdc: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_DisableBankForSubBg: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_DisableBankForSubObj: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_DisableBankForSubBgExtPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_DisableBankForSubObjExtPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    G2_GetBG0ScrPtr: Symbol[
        Optional[list[int]],
        None,
    ]

    G2S_GetBG0ScrPtr: Symbol[
        Optional[list[int]],
        None,
    ]

    G2_GetBG1ScrPtr: Symbol[
        Optional[list[int]],
        None,
    ]

    G2S_GetBG1ScrPtr: Symbol[
        Optional[list[int]],
        None,
    ]

    G2_GetBG2ScrPtr: Symbol[
        Optional[list[int]],
        None,
    ]

    G2_GetBG3ScrPtr: Symbol[
        Optional[list[int]],
        None,
    ]

    G2_GetBG0CharPtr: Symbol[
        Optional[list[int]],
        None,
    ]

    G2S_GetBG0CharPtr: Symbol[
        Optional[list[int]],
        None,
    ]

    G2_GetBG1CharPtr: Symbol[
        Optional[list[int]],
        None,
    ]

    G2S_GetBG1CharPtr: Symbol[
        Optional[list[int]],
        None,
    ]

    G2_GetBG2CharPtr: Symbol[
        Optional[list[int]],
        None,
    ]

    G2_GetBG3CharPtr: Symbol[
        Optional[list[int]],
        None,
    ]

    G2x_SetBlendAlpha: Symbol[
        Optional[list[int]],
        None,
    ]

    G2x_SetBlendBrightness: Symbol[
        Optional[list[int]],
        None,
    ]

    G2x_ChangeBlendBrightness: Symbol[
        Optional[list[int]],
        None,
    ]

    G3_LoadMtx44: Symbol[
        Optional[list[int]],
        None,
    ]

    G3_LoadMtx43: Symbol[
        Optional[list[int]],
        None,
    ]

    G3_MultMtx43: Symbol[
        Optional[list[int]],
        None,
    ]

    G3X_Init: Symbol[
        Optional[list[int]],
        None,
    ]

    G3X_Reset: Symbol[
        Optional[list[int]],
        None,
    ]

    G3X_ClearFifo: Symbol[
        Optional[list[int]],
        None,
    ]

    G3X_InitMtxStack: Symbol[
        Optional[list[int]],
        None,
    ]

    G3X_ResetMtxStack: Symbol[
        Optional[list[int]],
        None,
    ]

    G3X_SetClearColor: Symbol[
        Optional[list[int]],
        None,
    ]

    G3X_InitTable: Symbol[
        Optional[list[int]],
        None,
    ]

    G3X_GetMtxStackLevelPV: Symbol[
        Optional[list[int]],
        None,
    ]

    G3X_GetMtxStackLevelPJ: Symbol[
        Optional[list[int]],
        None,
    ]

    GXi_NopClearFifo128: Symbol[
        Optional[list[int]],
        None,
    ]

    G3i_OrthoW: Symbol[
        Optional[list[int]],
        None,
    ]

    G3i_LookAt: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_LoadBgPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    Gxs_LoadBgPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_LoadObjPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    Gxs_LoadObjPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_LoadOam: Symbol[
        Optional[list[int]],
        None,
    ]

    Gxs_LoadOam: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_LoadObj: Symbol[
        Optional[list[int]],
        None,
    ]

    Gxs_LoadObj: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_LoadBg0Scr: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_LoadBg1Scr: Symbol[
        Optional[list[int]],
        None,
    ]

    Gxs_LoadBg1Scr: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_LoadBg2Scr: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_LoadBg3Scr: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_LoadBg0Char: Symbol[
        Optional[list[int]],
        None,
    ]

    Gxs_LoadBg0Char: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_LoadBg1Char: Symbol[
        Optional[list[int]],
        None,
    ]

    Gxs_LoadBg1Char: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_LoadBg2Char: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_LoadBg3Char: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_BeginLoadBgExtPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_EndLoadBgExtPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_BeginLoadObjExtPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_EndLoadObjExtPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    Gxs_BeginLoadBgExtPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    Gxs_EndLoadBgExtPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    Gxs_BeginLoadObjExtPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    Gxs_EndLoadObjExtPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_BeginLoadTex: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_LoadTex: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_EndLoadTex: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_BeginLoadTexPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_LoadTexPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_EndLoadTexPltt: Symbol[
        Optional[list[int]],
        None,
    ]

    GeomGxFifoSendMtx4x3: Symbol[
        Optional[list[int]],
        None,
    ]

    GX_SendFifo64B: Symbol[
        Optional[list[int]],
        None,
    ]

    OS_GetLockID: Symbol[
        Optional[list[int]],
        None,
    ]

    IncrementThreadCount: Symbol[
        Optional[list[int]],
        None,
    ]

    InsertThreadIntoList: Symbol[
        Optional[list[int]],
        None,
    ]

    StartThread: Symbol[
        Optional[list[int]],
        None,
    ]

    ThreadExit: Symbol[
        Optional[list[int]],
        None,
    ]

    SetThreadField0xB4: Symbol[
        Optional[list[int]],
        None,
    ]

    InitThread: Symbol[
        Optional[list[int]],
        None,
    ]

    GetTimer0Control: Symbol[
        Optional[list[int]],
        None,
    ]

    ClearIrqFlag: Symbol[
        Optional[list[int]],
        None,
    ]

    EnableIrqFlag: Symbol[
        Optional[list[int]],
        None,
    ]

    SetIrqFlag: Symbol[
        Optional[list[int]],
        None,
    ]

    EnableIrqFiqFlags: Symbol[
        Optional[list[int]],
        None,
    ]

    SetIrqFiqFlags: Symbol[
        Optional[list[int]],
        None,
    ]

    GetIrqFlag: Symbol[
        Optional[list[int]],
        None,
    ]

    GetProcessorMode: Symbol[
        Optional[list[int]],
        None,
    ]

    GetDsFirmwareUserSettings: Symbol[
        Optional[list[int]],
        None,
    ]

    CountLeadingZeros: Symbol[
        Optional[list[int]],
        None,
    ]

    WaitForever2: Symbol[
        Optional[list[int]],
        None,
    ]

    WaitForInterrupt: Symbol[
        Optional[list[int]],
        None,
    ]

    ArrayFill16: Symbol[
        Optional[list[int]],
        None,
    ]

    ArrayCopy16: Symbol[
        Optional[list[int]],
        None,
    ]

    ArrayFill32: Symbol[
        Optional[list[int]],
        None,
    ]

    ArrayCopy32: Symbol[
        Optional[list[int]],
        None,
    ]

    ArrayFill32Fast: Symbol[
        Optional[list[int]],
        None,
    ]

    ArrayCopy32Fast: Symbol[
        Optional[list[int]],
        None,
    ]

    MemsetFast: Symbol[
        Optional[list[int]],
        None,
    ]

    MemcpyFast: Symbol[
        Optional[list[int]],
        None,
    ]

    AtomicExchange: Symbol[
        Optional[list[int]],
        None,
    ]

    FileInit: Symbol[
        Optional[list[int]],
        None,
    ]

    GetOverlayInfo: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadOverlayInternal: Symbol[
        Optional[list[int]],
        None,
    ]

    InitOverlay: Symbol[
        Optional[list[int]],
        None,
    ]

    abs: Symbol[
        Optional[list[int]],
        None,
    ]

    mbtowc: Symbol[
        Optional[list[int]],
        None,
    ]

    TryAssignByte: Symbol[
        Optional[list[int]],
        None,
    ]

    TryAssignByteWrapper: Symbol[
        Optional[list[int]],
        None,
    ]

    wcstombs: Symbol[
        Optional[list[int]],
        None,
    ]

    memcpy: Symbol[
        Optional[list[int]],
        None,
    ]

    memmove: Symbol[
        Optional[list[int]],
        None,
    ]

    memset: Symbol[
        Optional[list[int]],
        None,
    ]

    memchr: Symbol[
        Optional[list[int]],
        None,
    ]

    memcmp: Symbol[
        Optional[list[int]],
        None,
    ]

    memset_internal: Symbol[
        Optional[list[int]],
        None,
    ]

    __vsprintf_internal_slice: Symbol[
        Optional[list[int]],
        None,
    ]

    TryAppendToSlice: Symbol[
        Optional[list[int]],
        None,
    ]

    __vsprintf_internal: Symbol[
        Optional[list[int]],
        None,
    ]

    vsprintf: Symbol[
        Optional[list[int]],
        None,
    ]

    snprintf: Symbol[
        Optional[list[int]],
        None,
    ]

    sprintf: Symbol[
        Optional[list[int]],
        None,
    ]

    strlen: Symbol[
        Optional[list[int]],
        None,
    ]

    strcpy: Symbol[
        Optional[list[int]],
        None,
    ]

    strncpy: Symbol[
        Optional[list[int]],
        None,
    ]

    strcat: Symbol[
        Optional[list[int]],
        None,
    ]

    strncat: Symbol[
        Optional[list[int]],
        None,
    ]

    strcmp: Symbol[
        Optional[list[int]],
        None,
    ]

    strncmp: Symbol[
        Optional[list[int]],
        None,
    ]

    strchr: Symbol[
        Optional[list[int]],
        None,
    ]

    strcspn: Symbol[
        Optional[list[int]],
        None,
    ]

    strstr: Symbol[
        Optional[list[int]],
        None,
    ]

    wcslen: Symbol[
        Optional[list[int]],
        None,
    ]

    _dadd: Symbol[
        Optional[list[int]],
        None,
    ]

    _d2f: Symbol[
        Optional[list[int]],
        None,
    ]

    _ll_ufrom_d: Symbol[
        Optional[list[int]],
        None,
    ]

    _dflt: Symbol[
        Optional[list[int]],
        None,
    ]

    _dfltu: Symbol[
        Optional[list[int]],
        None,
    ]

    _dmul: Symbol[
        Optional[list[int]],
        None,
    ]

    _dsqrt: Symbol[
        Optional[list[int]],
        None,
    ]

    _dsub: Symbol[
        Optional[list[int]],
        None,
    ]

    _fadd: Symbol[
        Optional[list[int]],
        None,
    ]

    _dgeq: Symbol[
        Optional[list[int]],
        None,
    ]

    _dleq: Symbol[
        Optional[list[int]],
        None,
    ]

    _dls: Symbol[
        Optional[list[int]],
        None,
    ]

    _deq: Symbol[
        Optional[list[int]],
        None,
    ]

    _dneq: Symbol[
        Optional[list[int]],
        None,
    ]

    _fls: Symbol[
        Optional[list[int]],
        None,
    ]

    _fdiv: Symbol[
        Optional[list[int]],
        None,
    ]

    _f2d: Symbol[
        Optional[list[int]],
        None,
    ]

    _ffix: Symbol[
        Optional[list[int]],
        None,
    ]

    _fflt: Symbol[
        Optional[list[int]],
        None,
    ]

    _ffltu: Symbol[
        Optional[list[int]],
        None,
    ]

    _fmul: Symbol[
        Optional[list[int]],
        None,
    ]

    sqrtf: Symbol[
        Optional[list[int]],
        None,
    ]

    _fsub: Symbol[
        Optional[list[int]],
        None,
    ]

    _ll_mod: Symbol[
        Optional[list[int]],
        None,
    ]

    _ll_sdiv: Symbol[
        Optional[list[int]],
        None,
    ]

    _ll_udiv: Symbol[
        Optional[list[int]],
        None,
    ]

    _ull_mod: Symbol[
        Optional[list[int]],
        None,
    ]

    _ll_mul: Symbol[
        Optional[list[int]],
        None,
    ]

    _s32_div_f: Symbol[
        Optional[list[int]],
        None,
    ]

    _u32_div_f: Symbol[
        Optional[list[int]],
        None,
    ]

    _u32_div_not_0_f: Symbol[
        Optional[list[int]],
        None,
    ]

    _drdiv: Symbol[
        Optional[list[int]],
        None,
    ]

    _ddiv: Symbol[
        Optional[list[int]],
        None,
    ]

    _fp_init: Symbol[
        Optional[list[int]],
        None,
    ]


class LibsDataProtocol(Protocol):

    pass


LibsProtocol = SectionProtocol[
    LibsFunctionsProtocol,
    LibsDataProtocol,
    Optional[int],
]


class Move_effectsFunctionsProtocol(Protocol):

    DoMoveDamage: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveIronTail: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDamageMultihitUntilMiss: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveYawn: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSleep: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveNightmare: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveMorningSun: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveVitalThrow: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDig: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSweetScent: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveCharm: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveRainDance: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveHail: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveHealStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveBubble: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveEncore: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveRage: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSuperFang: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMovePainSplit: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveTorment: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveStringShot: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSwagger: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSnore: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveScreech: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDamageCringe30: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveWeatherBall: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveWhirlpool: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveFakeTears: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSpite: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveFocusEnergy: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSmokescreen: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveMirrorMove: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveOverheat: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveAuroraBeam: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveMemento: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveOctazooka: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveFlatter: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveWillOWisp: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveReturn: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveGrudge: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveCounter: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDamageBurn10FlameWheel: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDamageBurn10: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveExpose: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDoubleTeam: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveGust: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveBoostDefense1: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveParalyze: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveBoostAttack1: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveRazorWind: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveBide: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveBideUnleash: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveCrunch: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDamageCringe20: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDamageParalyze20: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveEndeavor: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveFacade: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDamageLowerSpeed20: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveBrickBreak: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDamageLowerSpeed100: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveFocusPunch: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDamageDrain: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveReversal: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSmellingSalt: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveMetalSound: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveTickle: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveShadowHold: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveHaze: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDamageMultihitFatigue: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDamageWeightDependent: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDamageBoostAllStats: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSynthesis: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveBoostSpeed1: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveRapidSpin: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSureShot: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveCosmicPower: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSkyAttack: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDamageFreeze15: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveMeteorMash: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveEndure: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveLowerSpeed1: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDamageConfuse10: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMovePsywave: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDamageLowerDefensiveStatVariable: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMovePsychoBoost: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveUproar: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveWaterSpout: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMovePsychUp: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDamageWithRecoil: Symbol[
        Optional[list[int]],
        None,
    ]

    EntityIsValidMoveEffects: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveRecoverHp: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveEarthquake: Symbol[
        Optional[list[int]],
        None,
    ]

    GetNaturePowerVariant: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveNaturePower: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDamageParalyze10: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSelfdestruct: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveShadowBall: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveCharge: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveThunderbolt: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveMist: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveFissure: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDamageCringe10: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSafeguard: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveAbsorb: Symbol[
        Optional[list[int]],
        None,
    ]

    DefenderAbilityIsActiveMoveEffects: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSkillSwap: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSketch: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveHeadbutt: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDoubleEdge: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSandstorm: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveLowerAccuracy1: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDamagePoison40: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveGrowth: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSacredFire: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveOhko: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSolarBeam: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSonicBoom: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveFly: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveExplosion: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDive: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveWaterfall: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDamageLowerAccuracy40: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveStockpile: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveTwister: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveTwineedle: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveRecoverHpTeam: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveMinimize: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSeismicToss: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveConfuse: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveTaunt: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveMoonlight: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveHornDrill: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSwordsDance: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveConversion: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveConversion2: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveHelpingHand: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveBoostDefense2: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveWarp: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveThundershock: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveThunderWave: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveZapCannon: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveBlock: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMovePoison: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveToxic: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMovePoisonFang: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDamagePoison18: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveJumpKick: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveBounce: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveHiJumpKick: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveTriAttack: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSwapItems: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveTripleKick: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSport: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveMudSlap: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDamageStealItem: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveAmnesia: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveNightShade: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveGrowl: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSurf: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveRolePlay: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSunnyDay: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveLowerDefense1: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveWish: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveFakeOut: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSleepTalk: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMovePayDay: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveAssist: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveRest: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveIngrain: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSwallow: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveCurse: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSuperpower: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSteelWing: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSpitUp: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDynamicPunch: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveKnockOff: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSplash: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSetDamage: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveBellyDrum: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveLightScreen: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSecretPower: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDamageConfuse30: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveBulkUp: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMovePause: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveFeatherDance: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveBeatUp: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveBlastBurn: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveCrushClaw: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveBlazeKick: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMovePresent: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveEruption: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveTransform: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMovePoisonTail: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveBlowback: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveCamouflage: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveTailGlow: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDamageConstrict10: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMovePerishSong: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveWrap: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSpikes: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveMagnitude: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveMagicCoat: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveProtect: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDefenseCurl: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDecoy: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveMistBall: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDestinyBond: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveMirrorCoat: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveCalmMind: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveHiddenPower: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveMetalClaw: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveAttract: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveCopycat: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveFrustration: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveLeechSeed: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveMetronome: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDreamEater: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSnatch: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveRecycle: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveReflect: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDragonRage: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDragonDance: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSkullBash: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDamageLowerSpecialDefense50: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveStruggle: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveRockSmash: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSeeTrap: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveTakeaway: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveRebound: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSwitchPositions: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveStayAway: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveCleanse: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSiesta: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveTwoEdge: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveNoMove: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveScan: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMovePowerEars: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveTransfer: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSlowDown: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSearchlight: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMovePetrify: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMovePounce: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveTrawl: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveEscape: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDrought: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveTrapBuster: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveWildCall: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveInvisify: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveOneShot: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveHpGauge: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveVacuumCut: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveReviver: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveShocker: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveEcho: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveFamish: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveOneRoom: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveFillIn: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveTrapper: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveItemize: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveHurl: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveMobile: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveSeeStairs: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveLongToss: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMovePierce: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveHammerArm: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveAquaRing: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveGastroAcid: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveHealingWish: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveCloseCombat: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveLuckyChant: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveGuardSwap: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveHealOrder: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveHealBlock: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveThunderFang: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDefog: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveTrumpCard: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveIceFang: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMovePsychoShift: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveEmbargo: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveBrine: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveNaturalGift: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveGyroBall: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveShadowForce: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveGravity: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveStealthRock: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveChargeBeam: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDamageEatItem: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveAcupressure: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveMagnetRise: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveToxicSpikes: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveLastResort: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveTrickRoom: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveWorrySeed: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDamageHpDependent: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveHeartSwap: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveRoost: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMovePowerSwap: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMovePowerTrick: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveFeint: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveFlareBlitz: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDefendOrder: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveFireFang: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveLunarDance: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveMiracleEye: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveWakeUpSlap: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveMetalBurst: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveHeadSmash: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveCaptivate: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveLeafStorm: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDracoMeteor: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveRockPolish: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveNastyPlot: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveTag0x1AB: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveTag0x1A6: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveTag0x1A7: Symbol[
        Optional[list[int]],
        None,
    ]


class Move_effectsDataProtocol(Protocol):

    MAX_HP_CAP_MOVE_EFFECTS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LUNAR_DANCE_PP_RESTORATION: Symbol[
        Optional[list[int]],
        Optional[int],
    ]


Move_effectsProtocol = SectionProtocol[
    Move_effectsFunctionsProtocol,
    Move_effectsDataProtocol,
    Optional[int],
]


class Overlay0FunctionsProtocol(Protocol):

    pass


class Overlay0DataProtocol(Protocol):

    TOP_MENU_MUSIC_ID: Symbol[
        Optional[list[int]],
        None,
    ]


Overlay0Protocol = SectionProtocol[
    Overlay0FunctionsProtocol,
    Overlay0DataProtocol,
    Optional[int],
]


class Overlay1FunctionsProtocol(Protocol):

    CreateMainMenus: Symbol[
        Optional[list[int]],
        None,
    ]

    AddMainMenuOption: Symbol[
        Optional[list[int]],
        None,
    ]

    AddSubMenuOption: Symbol[
        Optional[list[int]],
        None,
    ]

    ProcessContinueScreenContents: Symbol[
        Optional[list[int]],
        None,
    ]


class Overlay1DataProtocol(Protocol):

    PRINTS_STRINGS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    PRINTS_STRUCT: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MAIN_MENU_WINDOW_PARAMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MAIN_MENU_WINDOW_PARAMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MAIN_MENU_WINDOW_PARAMS_3: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MAIN_MENU_WINDOW_PARAMS_4: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    CONTINUE_CHOICE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SUBMENU: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MAIN_MENU: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MAIN_MENU_WINDOW_PARAMS_5: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MAIN_MENU_WINDOW_PARAMS_6: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MAIN_MENU_WINDOW_PARAMS_7: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MAIN_MENU_ITEMS_CONFIRM: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MAIN_MENU_WINDOW_PARAMS_8: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MAIN_MENU_WINDOW_PARAMS_9: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MAIN_DEBUG_MENU_ITEMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MAIN_MENU_WINDOW_PARAMS_10: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MAIN_DEBUG_MENU_ITEMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]


Overlay1Protocol = SectionProtocol[
    Overlay1FunctionsProtocol,
    Overlay1DataProtocol,
    Optional[int],
]


class Overlay10FunctionsProtocol(Protocol):

    CreateInventoryMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    SetInventoryMenuState0: Symbol[
        Optional[list[int]],
        None,
    ]

    SetInventoryMenuState6: Symbol[
        Optional[list[int]],
        None,
    ]

    CloseInventoryMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    IsInventoryMenuActive: Symbol[
        Optional[list[int]],
        None,
    ]

    CheckInventoryMenuField0x1A0: Symbol[
        Optional[list[int]],
        None,
    ]

    PopInventoryMenuField0x1A3: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateInventoryMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    IsInventoryMenuState3: Symbol[
        Optional[list[int]],
        None,
    ]

    SprintfStatic: Symbol[
        Optional[list[int]],
        None,
    ]

    GetEffectAnimationField0x19: Symbol[
        Optional[list[int]],
        None,
    ]

    AnimationHasMoreFrames: Symbol[
        Optional[list[int]],
        None,
    ]

    GetEffectAnimation: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMoveAnimation: Symbol[
        Optional[list[int]],
        None,
    ]

    GetSpecialMonsterMoveAnimation: Symbol[
        Optional[list[int]],
        None,
    ]

    GetTrapAnimation: Symbol[
        Optional[list[int]],
        None,
    ]

    GetItemAnimation1: Symbol[
        Optional[list[int]],
        None,
    ]

    GetItemAnimation2: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMoveAnimationSpeed: Symbol[
        Optional[list[int]],
        None,
    ]

    DrawTeamStats: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateTeamStats: Symbol[
        Optional[list[int]],
        None,
    ]

    FreeTeamStats: Symbol[
        Optional[list[int]],
        None,
    ]

    FreeMapAndTeam: Symbol[
        Optional[list[int]],
        None,
    ]

    ProcessTeamStatsLvHp: Symbol[
        Optional[list[int]],
        None,
    ]

    ProcessTeamStatsNameGender: Symbol[
        Optional[list[int]],
        None,
    ]

    IsBackgroundTileset: Symbol[
        Optional[list[int]],
        None,
    ]

    InitTilesetBuffer: Symbol[
        Optional[list[int]],
        None,
    ]

    MainGame: Symbol[
        Optional[list[int]],
        None,
    ]


class Overlay10DataProtocol(Protocol):

    INVENTORY_MENU_DEFAULT_WINDOW_PARAMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    FIRST_DUNGEON_WITH_MONSTER_HOUSE_TRAPS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BAD_POISON_DAMAGE_COOLDOWN: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    PROTEIN_STAT_BOOST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    WATERFALL_CRINGE_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    AURORA_BEAM_LOWER_ATTACK_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SPAWN_CAP_NO_MONSTER_HOUSE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OREN_BERRY_DAMAGE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    IRON_TAIL_LOWER_DEFENSE_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TWINEEDLE_POISON_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EXTRASENSORY_CRINGE_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ROCK_SLIDE_CRINGE_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    CRUNCH_LOWER_DEFENSE_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    FOREWARN_FORCED_MISS_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    UNOWN_STONE_DROP_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SITRUS_BERRY_HP_RESTORATION: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MUDDY_WATER_LOWER_ACCURACY_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SILVER_WIND_BOOST_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    POISON_TAIL_POISON_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    THUNDERSHOCK_PARALYZE_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BOUNCE_PARALYZE_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    HEADBUTT_CRINGE_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    FIRE_FANG_CRINGE_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SACRED_FIRE_BURN_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    WHIRLPOOL_CONSTRICTION_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EXP_ELITE_EXP_BOOST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MONSTER_HOUSE_MAX_NON_MONSTER_SPAWNS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    HEAL_ORDER_HP_RESTORATION: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STEEL_WING_BOOST_DEFENSE_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    GOLD_THORN_POWER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BURN_DAMAGE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    POISON_DAMAGE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SPAWN_COOLDOWN: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MIST_BALL_LOWER_SPECIAL_ATTACK_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    CHARGE_BEAM_BOOST_SPECIAL_ATTACK_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ORAN_BERRY_FULL_HP_BOOST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LIFE_SEED_HP_BOOST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OCTAZOOKA_LOWER_ACCURACY_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LUSTER_PURGE_LOWER_SPECIAL_DEFENSE_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SUPER_LUCK_CRIT_RATE_BOOST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    CONSTRICT_LOWER_SPEED_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ICE_FANG_FREEZE_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SMOG_POISON_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LICK_PARALYZE_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    THUNDER_FANG_PARALYZE_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BITE_CRINGE_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SKY_ATTACK_CRINGE_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ICE_FANG_CRINGE_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BLAZE_KICK_BURN_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    FLAMETHROWER_BURN_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DIZZY_PUNCH_CONFUSE_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SECRET_POWER_EFFECT_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    METAL_CLAW_BOOST_ATTACK_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TECHNICIAN_MOVE_POWER_THRESHOLD: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SONICBOOM_FIXED_DAMAGE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RAIN_ABILITY_BONUS_REGEN: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LEECH_SEED_HP_DRAIN: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EXCLUSIVE_ITEM_EXP_BOOST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    AFTERMATH_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SET_DAMAGE_STATUS_DAMAGE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    INTIMIDATOR_ACTIVATION_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TYPE_ADVANTAGE_MASTER_CRIT_RATE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ORAN_BERRY_HP_RESTORATION: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SITRUS_BERRY_FULL_HP_BOOST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SNORE_CRINGE_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    METEOR_MASH_BOOST_ATTACK_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    CRUSH_CLAW_LOWER_DEFENSE_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BURN_DAMAGE_COOLDOWN: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SHADOW_BALL_LOWER_SPECIAL_DEFENSE_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STICK_POWER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BUBBLE_LOWER_SPEED_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ICE_BODY_BONUS_REGEN: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    POWDER_SNOW_FREEZE_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    POISON_STING_POISON_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SPAWN_COOLDOWN_THIEF_ALERT: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    POISON_FANG_POISON_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    WEATHER_MOVE_TURN_COUNT: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    THUNDER_PARALYZE_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    THUNDERBOLT_PARALYZE_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MONSTER_HOUSE_MAX_MONSTER_SPAWNS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TWISTER_CRINGE_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SPEED_BOOST_TURNS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    FAKE_OUT_CRINGE_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    THUNDER_FANG_CRINGE_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    FLARE_BLITZ_BURN_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    FLAME_WHEEL_BURN_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    PSYBEAM_CONFUSE_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TRI_ATTACK_STATUS_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MIRACLE_CHEST_EXP_BOOST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    WONDER_CHEST_EXP_BOOST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SPAWN_CAP_WITH_MONSTER_HOUSE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    POISON_DAMAGE_COOLDOWN: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LEECH_SEED_DAMAGE_COOLDOWN: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    THROWN_ITEM_HIT_CHANCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    GEO_PEBBLE_DAMAGE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    GRAVELEROCK_DAMAGE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RARE_FOSSIL_DAMAGE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    GINSENG_CHANCE_3: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ZINC_STAT_BOOST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    IRON_STAT_BOOST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    CALCIUM_STAT_BOOST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    WISH_BONUS_REGEN: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DRAGON_RAGE_FIXED_DAMAGE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    CORSOLA_TWIG_POWER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    CACNEA_SPIKE_POWER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    GOLD_FANG_POWER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SILVER_SPIKE_POWER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    IRON_THORN_POWER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SCOPE_LENS_CRIT_RATE_BOOST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    HEALING_WISH_HP_RESTORATION: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ME_FIRST_MULTIPLIER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    FACADE_DAMAGE_MULTIPLIER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    IMPRISON_TURN_RANGE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SLEEP_TURN_RANGE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    NIGHTMARE_TURN_RANGE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BURN_DAMAGE_MULTIPLIER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    REST_TURN_RANGE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MATCHUP_SUPER_EFFECTIVE_MULTIPLIER_ERRATIC_PLAYER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MATCHUP_IMMUNE_MULTIPLIER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SPORT_CONDITION_TURN_RANGE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SURE_SHOT_TURN_RANGE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DETECT_BAND_MOVE_ACCURACY_DROP: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TINTED_LENS_MULTIPLIER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SMOKESCREEN_TURN_RANGE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    PERISH_SONG_TURN_RANGE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SHADOW_FORCE_DAMAGE_MULTIPLIER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DIG_DAMAGE_MULTIPLIER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DIVE_DAMAGE_MULTIPLIER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BOUNCE_DAMAGE_MULTIPLIER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    POWER_PITCHER_DAMAGE_MULTIPLIER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    QUICK_DODGER_MOVE_ACCURACY_DROP: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MATCHUP_NOT_VERY_EFFECTIVE_MULTIPLIER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MATCHUP_SUPER_EFFECTIVE_MULTIPLIER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MATCHUP_NEUTRAL_MULTIPLIER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MATCHUP_IMMUNE_MULTIPLIER_ERRATIC_PLAYER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MATCHUP_NOT_VERY_EFFECTIVE_MULTIPLIER_ERRATIC_PLAYER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MATCHUP_NEUTRAL_MULTIPLIER_ERRATIC_PLAYER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    AIR_BLADE_DAMAGE_MULTIPLIER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    KECLEON_SHOP_BOOST_CHANCE_MULTIPLIER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    HIDDEN_STAIRS_SPAWN_CHANCE_MULTIPLIER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    YAWN_TURN_RANGE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SPEED_BOOST_TURN_RANGE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SOLARBEAM_DAMAGE_MULTIPLIER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SKY_ATTACK_DAMAGE_MULTIPLIER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RAZOR_WIND_DAMAGE_MULTIPLIER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    FOCUS_PUNCH_DAMAGE_MULTIPLIER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SKULL_BASH_DAMAGE_MULTIPLIER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    FLY_DAMAGE_MULTIPLIER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    WEATHER_BALL_TYPE_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LAST_RESORT_DAMAGE_MULT_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SYNTHESIS_HP_RESTORATION_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ROOST_HP_RESTORATION_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MOONLIGHT_HP_RESTORATION_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MORNING_SUN_HP_RESTORATION_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    REVERSAL_DAMAGE_MULT_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    WATER_SPOUT_DAMAGE_MULT_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    WRING_OUT_DAMAGE_MULT_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ERUPTION_DAMAGE_MULT_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    WEATHER_BALL_DAMAGE_MULT_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EAT_ITEM_EFFECT_IGNORE_LIST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    CASTFORM_WEATHER_ATTRIBUTE_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BAD_POISON_DAMAGE_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TYPE_MATCHUP_COMBINATOR_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OFFENSIVE_STAT_STAGE_MULTIPLIERS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DEFENSIVE_STAT_STAGE_MULTIPLIERS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    NATURE_POWER_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    APPLES_AND_BERRIES_ITEM_IDS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RECRUITMENT_LEVEL_BOOST_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    NATURAL_GIFT_ITEM_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RANDOM_MUSIC_ID_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SHOP_ITEM_CHANCES: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MALE_ACCURACY_STAGE_MULTIPLIERS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MALE_EVASION_STAGE_MULTIPLIERS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    FEMALE_ACCURACY_STAGE_MULTIPLIERS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    FEMALE_EVASION_STAGE_MULTIPLIERS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MUSIC_ID_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TYPE_MATCHUP_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    FIXED_ROOM_MONSTER_SPAWN_STATS_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    METRONOME_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TILESET_PROPERTIES: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    FIXED_ROOM_PROPERTIES_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TRAP_ANIMATION_INFO: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ITEM_ANIMATION_INFO: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MOVE_ANIMATION_INFO: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EFFECT_ANIMATION_INFO: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SPECIAL_MONSTER_MOVE_ANIMATION_INFO: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DEFEAT_ITEM_LOSS_CHANCE: Symbol[
        Optional[list[int]],
        None,
    ]


Overlay10Protocol = SectionProtocol[
    Overlay10FunctionsProtocol,
    Overlay10DataProtocol,
    Optional[int],
]


class Overlay11FunctionsProtocol(Protocol):

    UnlockScriptingLock: Symbol[
        Optional[list[int]],
        None,
    ]

    FuncThatCallsRunNextOpcode: Symbol[
        Optional[list[int]],
        None,
    ]

    RunNextOpcode: Symbol[
        Optional[list[int]],
        None,
    ]

    HandleUnlocks: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadFileFromRomVeneer: Symbol[
        Optional[list[int]],
        None,
    ]

    SsbLoad2: Symbol[
        Optional[list[int]],
        None,
    ]

    ScriptParamToInt: Symbol[
        Optional[list[int]],
        None,
    ]

    ScriptParamToFixedPoint16: Symbol[
        Optional[list[int]],
        None,
    ]

    StationLoadHanger: Symbol[
        Optional[list[int]],
        None,
    ]

    ScriptStationLoadTalk: Symbol[
        Optional[list[int]],
        None,
    ]

    SsbLoad1: Symbol[
        Optional[list[int]],
        None,
    ]

    ScriptSpecialProcessCall: Symbol[
        Optional[list[int]],
        None,
    ]

    GetCoroutineInfo: Symbol[
        Optional[list[int]],
        None,
    ]

    GetSpecialRecruitmentSpecies: Symbol[
        Optional[list[int]],
        None,
    ]

    PrepareMenuAcceptTeamMember: Symbol[
        Optional[list[int]],
        None,
    ]

    InitRandomNpcJobs: Symbol[
        Optional[list[int]],
        None,
    ]

    GetRandomNpcJobType: Symbol[
        Optional[list[int]],
        None,
    ]

    GetRandomNpcJobSubtype: Symbol[
        Optional[list[int]],
        None,
    ]

    GetRandomNpcJobStillAvailable: Symbol[
        Optional[list[int]],
        None,
    ]

    AcceptRandomNpcJob: Symbol[
        Optional[list[int]],
        None,
    ]

    GroundMainLoop: Symbol[
        Optional[list[int]],
        None,
    ]

    GetAllocArenaGround: Symbol[
        Optional[list[int]],
        None,
    ]

    GetFreeArenaGround: Symbol[
        Optional[list[int]],
        None,
    ]

    GroundMainReturnDungeon: Symbol[
        Optional[list[int]],
        None,
    ]

    GroundMainNextDay: Symbol[
        Optional[list[int]],
        None,
    ]

    JumpToTitleScreen: Symbol[
        Optional[list[int]],
        None,
    ]

    ReturnToTitleScreen: Symbol[
        Optional[list[int]],
        None,
    ]

    ScriptSpecialProcess0x16: Symbol[
        Optional[list[int]],
        None,
    ]

    IsScreenFadeInProgress: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadBackgroundAttributes: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadMapType10: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadMapType11: Symbol[
        Optional[list[int]],
        None,
    ]

    GetSpecialLayoutBackground: Symbol[
        Optional[list[int]],
        None,
    ]

    SetAnimDataFields: Symbol[
        Optional[list[int]],
        None,
    ]

    SetAnimDataFieldsWrapper: Symbol[
        Optional[list[int]],
        None,
    ]

    InitAnimDataFromOtherAnimData: Symbol[
        Optional[list[int]],
        None,
    ]

    SetAnimDataFields2: Symbol[
        Optional[list[int]],
        None,
    ]

    GetIdleAnimationType: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadObjectAnimData: Symbol[
        Optional[list[int]],
        None,
    ]

    InitAnimDataFromOtherAnimDataVeneer: Symbol[
        Optional[list[int]],
        None,
    ]

    AnimRelatedFunction: Symbol[
        Optional[list[int]],
        None,
    ]

    AllocAndInitPartnerFollowDataAndLiveActorList: Symbol[
        Optional[list[int]],
        None,
    ]

    InitPartnerFollowDataAndLiveActorList: Symbol[
        Optional[list[int]],
        None,
    ]

    DeleteLiveActor: Symbol[
        Optional[list[int]],
        None,
    ]

    ChangeActorAnimation: Symbol[
        Optional[list[int]],
        None,
    ]

    InitPartnerFollowData: Symbol[
        Optional[list[int]],
        None,
    ]

    GetDirectionLiveActor: Symbol[
        Optional[list[int]],
        None,
    ]

    SetDirectionLiveActor: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateTeamInfoBox: Symbol[
        Optional[list[int]],
        None,
    ]

    CloseTeamInfoBox: Symbol[
        Optional[list[int]],
        None,
    ]

    IsTeamInfoBoxActive: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateTeamInfoBox: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateTopGroundMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    CloseTopGroundMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateTopGroundMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    IsBagNotEmpty: Symbol[
        Optional[list[int]],
        None,
    ]

    SprintfStatic: Symbol[
        Optional[list[int]],
        None,
    ]

    GetExclusiveItemRequirements: Symbol[
        Optional[list[int]],
        None,
    ]

    HandleControlsTopScreenGround: Symbol[
        Optional[list[int]],
        None,
    ]

    GetDungeonMapPos: Symbol[
        Optional[list[int]],
        None,
    ]

    WorldMapSetMode: Symbol[
        Optional[list[int]],
        None,
    ]

    WorldMapSetCamera: Symbol[
        Optional[list[int]],
        None,
    ]

    StatusUpdate: Symbol[
        Optional[list[int]],
        None,
    ]

    HandleTeamStatsGround: Symbol[
        Optional[list[int]],
        None,
    ]


class Overlay11DataProtocol(Protocol):

    OVERLAY11_UNKNOWN_TABLE__NA_2316A38: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SCRIPT_COMMAND_PARSING_DATA: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SCRIPT_OP_CODE_NAMES: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SCRIPT_OP_CODES: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY11_DEBUG_STRINGS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    C_ROUTINE_NAMES: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    C_ROUTINES: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    GROUND_WEATHER_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    GROUND_WAN_FILES_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OBJECTS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RECRUITMENT_TABLE_LOCATIONS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RECRUITMENT_TABLE_LEVELS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RECRUITMENT_TABLE_SPECIES: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LEVEL_TILEMAP_LIST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SETANIMATION_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TEAM_INFO_BOX_DEFAULT_WINDOW_PARAMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY11_OVERLAY_LOAD_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    UNIONALL_RAM_ADDRESS: Symbol[
        Optional[list[int]],
        None,
    ]

    GROUND_STATE_MAP: Symbol[
        Optional[list[int]],
        None,
    ]

    GROUND_STATE_WEATHER: Symbol[
        Optional[list[int]],
        None,
    ]

    GROUND_STATE_PTRS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    WORLD_MAP_MODE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]


Overlay11Protocol = SectionProtocol[
    Overlay11FunctionsProtocol,
    Overlay11DataProtocol,
    Optional[int],
]


class Overlay12FunctionsProtocol(Protocol):

    pass


class Overlay12DataProtocol(Protocol):

    pass


Overlay12Protocol = SectionProtocol[
    Overlay12FunctionsProtocol,
    Overlay12DataProtocol,
    Optional[int],
]


class Overlay13FunctionsProtocol(Protocol):

    EntryOverlay13: Symbol[
        Optional[list[int]],
        None,
    ]

    ExitOverlay13: Symbol[
        Optional[list[int]],
        None,
    ]

    Overlay13SwitchFunctionNa238A1C8: Symbol[
        Optional[list[int]],
        None,
    ]

    Overlay13SwitchFunctionNa238A574: Symbol[
        Optional[list[int]],
        None,
    ]

    GetPersonality: Symbol[
        Optional[list[int]],
        None,
    ]

    GetOptionStringFromID: Symbol[
        Optional[list[int]],
        None,
    ]

    WaitForNextStep: Symbol[
        Optional[list[int]],
        None,
    ]


class Overlay13DataProtocol(Protocol):

    QUIZ_BORDER_COLOR_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    PORTRAIT_ATTRIBUTES: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    QUIZ_MALE_FEMALE_BOOST_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY13_UNKNOWN_STRUCT__NA_238C024: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    QUIZ_WINDOW_PARAMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    QUIZ_WINDOW_PARAMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    QUIZ_WINDOW_PARAMS_3: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    QUIZ_WINDOW_PARAMS_4: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    QUIZ_MENU_ITEMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STARTERS_PARTNER_IDS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STARTERS_HERO_IDS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STARTERS_TYPE_INCOMPATIBILITY_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STARTERS_STRINGS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    QUIZ_QUESTION_STRINGS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    QUIZ_ANSWER_STRINGS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    QUIZ_ANSWER_POINTS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY13_RESERVED_SPACE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY13_UNKNOWN_POINTER__NA_238CEA0: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY13_UNKNOWN_POINTER__NA_238CEA4: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY13_UNKNOWN_POINTER__NA_238CEA8: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    QUIZ_WINDOW_PARAMS_5: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    QUIZ_WINDOW_PARAMS_6: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    QUIZ_DEBUG_MENU_ITEMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY13_UNKNOWN_STRUCT__NA_238CF14: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    QUIZ_QUESTION_ANSWER_ASSOCIATIONS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]


Overlay13Protocol = SectionProtocol[
    Overlay13FunctionsProtocol,
    Overlay13DataProtocol,
    Optional[int],
]


class Overlay14FunctionsProtocol(Protocol):

    SentrySetupState: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryUpdateDisplay: Symbol[
        Optional[list[int]],
        None,
    ]

    SentrySetExitingState: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryRunState: Symbol[
        Optional[list[int]],
        None,
    ]

    SentrySetStateIntermediate: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryState0: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryState1: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryState2: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryState3: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryState4: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryStateExit: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryState6: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryState7: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryState8: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryState9: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryStateA: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryStateB: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryStateGenerateChoices: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryStateGetUserChoice: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryStateFinalizeRound: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryStateF: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryState10: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryState11: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryState12: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryState13: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryState14: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryState15: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryState16: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryState17: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryState18: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryState19: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryState1A: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryStateFinalizePoints: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryState1C: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryState1D: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryState1E: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryState1F: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryState20: Symbol[
        Optional[list[int]],
        None,
    ]

    SentryState21: Symbol[
        Optional[list[int]],
        None,
    ]


class Overlay14DataProtocol(Protocol):

    SENTRY_DUTY_STRUCT_SIZE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SENTRY_LOUDRED_MONSTER_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_ID_SENTRY_TOP_SESSIONS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_ID_SENTRY_INSTRUCTIONS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_ID_SENTRY_HERE_COMES: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_ID_SENTRY_WHOSE_FOOTPRINT: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_ID_SENTRY_TRY_AGAIN: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_ID_SENTRY_OUT_OF_TIME: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_ID_SENTRY_FOOTPRINT_IS_6EE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_ID_SENTRY_COME_IN_6EF: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_ID_SENTRY_WRONG: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_ID_SENTRY_BUCK_UP: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_ID_SENTRY_FOOTPRINT_IS_6EC: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_ID_SENTRY_COME_IN_6ED: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_ID_SENTRY_KEEP_YOU_WAITING: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_ID_SENTRY_THATLL_DO_IT: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SENTRY_CHATOT_MONSTER_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_ID_SENTRY_NO_MORE_VISITORS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STRING_ID_SENTRY_THATS_ALL: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SENTRY_GROVYLE_MONSTER_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SENTRY_DEBUG_MENU_ITEMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SENTRY_DUTY_PTR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SENTRY_DUTY_STATE_HANDLER_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]


Overlay14Protocol = SectionProtocol[
    Overlay14FunctionsProtocol,
    Overlay14DataProtocol,
    Optional[int],
]


class Overlay15FunctionsProtocol(Protocol):

    pass


class Overlay15DataProtocol(Protocol):

    BANK_MAIN_MENU_ITEMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BANK_WINDOW_PARAMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BANK_WINDOW_PARAMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BANK_WINDOW_PARAMS_3: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BANK_WINDOW_PARAMS_4: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BANK_WINDOW_PARAMS_5: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY15_RESERVED_SPACE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY15_UNKNOWN_POINTER__NA_238B180: Symbol[
        Optional[list[int]],
        Optional[int],
    ]


Overlay15Protocol = SectionProtocol[
    Overlay15FunctionsProtocol,
    Overlay15DataProtocol,
    Optional[int],
]


class Overlay16FunctionsProtocol(Protocol):

    pass


class Overlay16DataProtocol(Protocol):

    EVO_MENU_ITEMS_CONFIRM: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EVO_SUBMENU_ITEMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EVO_MAIN_MENU_ITEMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EVO_MENU_STRING_IDS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EVO_WINDOW_PARAMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EVO_WINDOW_PARAMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EVO_WINDOW_PARAMS_3: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EVO_WINDOW_PARAMS_4: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EVO_WINDOW_PARAMS_5: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EVO_WINDOW_PARAMS_6: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EVO_WINDOW_PARAMS_7: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY16_RESERVED_SPACE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY16_UNKNOWN_POINTER__NA_238CE40: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY16_UNKNOWN_POINTER__NA_238CE58: Symbol[
        Optional[list[int]],
        Optional[int],
    ]


Overlay16Protocol = SectionProtocol[
    Overlay16FunctionsProtocol,
    Overlay16DataProtocol,
    Optional[int],
]


class Overlay17FunctionsProtocol(Protocol):

    pass


class Overlay17DataProtocol(Protocol):

    ASSEMBLY_WINDOW_PARAMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ASSEMBLY_WINDOW_PARAMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ASSEMBLY_WINDOW_PARAMS_3: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ASSEMBLY_WINDOW_PARAMS_4: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ASSEMBLY_WINDOW_PARAMS_5: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ASSEMBLY_MENU_ITEMS_CONFIRM: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ASSEMBLY_MAIN_MENU_ITEMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ASSEMBLY_MAIN_MENU_ITEMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ASSEMBLY_SUBMENU_ITEMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ASSEMBLY_SUBMENU_ITEMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ASSEMBLY_SUBMENU_ITEMS_3: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ASSEMBLY_SUBMENU_ITEMS_4: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ASSEMBLY_SUBMENU_ITEMS_5: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ASSEMBLY_SUBMENU_ITEMS_6: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ASSEMBLY_SUBMENU_ITEMS_7: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY17_FUNCTION_POINTER_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY17_RESERVED_SPACE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY17_UNKNOWN_POINTER__NA_238BE00: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY17_UNKNOWN_POINTER__NA_238BE04: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY17_UNKNOWN_POINTER__NA_238BE08: Symbol[
        Optional[list[int]],
        Optional[int],
    ]


Overlay17Protocol = SectionProtocol[
    Overlay17FunctionsProtocol,
    Overlay17DataProtocol,
    Optional[int],
]


class Overlay18FunctionsProtocol(Protocol):

    pass


class Overlay18DataProtocol(Protocol):

    LINK_SHOP_WINDOW_PARAMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LINK_SHOP_WINDOW_PARAMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LINK_SHOP_WINDOW_PARAMS_3: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LINK_SHOP_WINDOW_PARAMS_4: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LINK_SHOP_WINDOW_PARAMS_5: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LINK_SHOP_WINDOW_PARAMS_6: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LINK_SHOP_WINDOW_PARAMS_7: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LINK_SHOP_WINDOW_PARAMS_8: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LINK_SHOP_WINDOW_PARAMS_9: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LINK_SHOP_WINDOW_PARAMS_10: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LINK_SHOP_WINDOW_PARAMS_11: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LINK_SHOP_MENU_ITEMS_CONFIRM: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LINK_SHOP_SUBMENU_ITEMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LINK_SHOP_SUBMENU_ITEMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LINK_SHOP_MAIN_MENU_ITEMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LINK_SHOP_SUBMENU_ITEMS_3: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LINK_SHOP_SUBMENU_ITEMS_4: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LINK_SHOP_SUBMENU_ITEMS_5: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LINK_SHOP_SUBMENU_ITEMS_6: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LINK_SHOP_SUBMENU_ITEMS_7: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY18_FUNCTION_POINTER_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY18_RESERVED_SPACE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY18_UNKNOWN_POINTER__NA_238D620: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY18_UNKNOWN_POINTER__NA_238D624: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY18_UNKNOWN_POINTER__NA_238D628: Symbol[
        Optional[list[int]],
        Optional[int],
    ]


Overlay18Protocol = SectionProtocol[
    Overlay18FunctionsProtocol,
    Overlay18DataProtocol,
    Optional[int],
]


class Overlay19FunctionsProtocol(Protocol):

    GetBarItem: Symbol[
        Optional[list[int]],
        None,
    ]

    GetRecruitableMonsterAll: Symbol[
        Optional[list[int]],
        None,
    ]

    GetRecruitableMonsterList: Symbol[
        Optional[list[int]],
        None,
    ]

    GetRecruitableMonsterListRestricted: Symbol[
        Optional[list[int]],
        None,
    ]


class Overlay19DataProtocol(Protocol):

    OVERLAY19_UNKNOWN_TABLE__NA_238DAE0: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BAR_UNLOCKABLE_DUNGEONS_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BAR_RECRUITABLE_MONSTER_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BAR_AVAILABLE_ITEMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY19_UNKNOWN_STRING_IDS__NA_238E178: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY19_UNKNOWN_STRUCT__NA_238E1A4: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY19_UNKNOWN_STRING_IDS__NA_238E1CC: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BAR_WINDOW_PARAMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BAR_WINDOW_PARAMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BAR_WINDOW_PARAMS_3: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BAR_MENU_ITEMS_CONFIRM_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BAR_MENU_ITEMS_CONFIRM_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY19_UNKNOWN_STRING_IDS__NA_238E238: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BAR_MAIN_MENU_ITEMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BAR_SUBMENU_ITEMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BAR_SUBMENU_ITEMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY19_RESERVED_SPACE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY19_UNKNOWN_POINTER__NA_238E360: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY19_UNKNOWN_POINTER__NA_238E364: Symbol[
        Optional[list[int]],
        Optional[int],
    ]


Overlay19Protocol = SectionProtocol[
    Overlay19FunctionsProtocol,
    Overlay19DataProtocol,
    Optional[int],
]


class Overlay2FunctionsProtocol(Protocol):

    pass


class Overlay2DataProtocol(Protocol):

    pass


Overlay2Protocol = SectionProtocol[
    Overlay2FunctionsProtocol,
    Overlay2DataProtocol,
    Optional[int],
]


class Overlay20FunctionsProtocol(Protocol):

    pass


class Overlay20DataProtocol(Protocol):

    OVERLAY20_UNKNOWN_POINTER__NA_238CF7C: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RECYCLE_MENU_ITEMS_CONFIRM_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RECYCLE_MENU_ITEMS_CONFIRM_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RECYCLE_SUBMENU_ITEMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RECYCLE_SUBMENU_ITEMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RECYCLE_MAIN_MENU_ITEMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY20_UNKNOWN_TABLE__NA_238D014: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RECYCLE_WINDOW_PARAMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RECYCLE_WINDOW_PARAMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RECYCLE_WINDOW_PARAMS_3: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RECYCLE_WINDOW_PARAMS_4: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RECYCLE_WINDOW_PARAMS_5: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RECYCLE_WINDOW_PARAMS_6: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RECYCLE_MAIN_MENU_ITEMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RECYCLE_WINDOW_PARAMS_7: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RECYCLE_WINDOW_PARAMS_8: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RECYCLE_WINDOW_PARAMS_9: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RECYCLE_WINDOW_PARAMS_10: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RECYCLE_WINDOW_PARAMS_11: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RECYCLE_MAIN_MENU_ITEMS_3: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY20_RESERVED_SPACE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY20_UNKNOWN_POINTER__NA_238D120: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY20_UNKNOWN_POINTER__NA_238D124: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY20_UNKNOWN_POINTER__NA_238D128: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY20_UNKNOWN_POINTER__NA_238D12C: Symbol[
        Optional[list[int]],
        Optional[int],
    ]


Overlay20Protocol = SectionProtocol[
    Overlay20FunctionsProtocol,
    Overlay20DataProtocol,
    Optional[int],
]


class Overlay21FunctionsProtocol(Protocol):

    pass


class Overlay21DataProtocol(Protocol):

    SWAP_SHOP_WINDOW_PARAMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SWAP_SHOP_MENU_ITEMS_CONFIRM: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SWAP_SHOP_SUBMENU_ITEMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SWAP_SHOP_SUBMENU_ITEMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SWAP_SHOP_MAIN_MENU_ITEMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SWAP_SHOP_MAIN_MENU_ITEMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SWAP_SHOP_SUBMENU_ITEMS_3: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY21_UNKNOWN_STRING_IDS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SWAP_SHOP_WINDOW_PARAMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SWAP_SHOP_WINDOW_PARAMS_3: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SWAP_SHOP_WINDOW_PARAMS_4: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SWAP_SHOP_WINDOW_PARAMS_5: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SWAP_SHOP_WINDOW_PARAMS_6: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SWAP_SHOP_WINDOW_PARAMS_7: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SWAP_SHOP_WINDOW_PARAMS_8: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SWAP_SHOP_WINDOW_PARAMS_9: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY21_JP_STRING: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY21_RESERVED_SPACE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY21_UNKNOWN_POINTER__NA_238CF40: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY21_UNKNOWN_POINTER__NA_238CF44: Symbol[
        Optional[list[int]],
        Optional[int],
    ]


Overlay21Protocol = SectionProtocol[
    Overlay21FunctionsProtocol,
    Overlay21DataProtocol,
    Optional[int],
]


class Overlay22FunctionsProtocol(Protocol):

    pass


class Overlay22DataProtocol(Protocol):

    SHOP_WINDOW_PARAMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SHOP_WINDOW_PARAMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY22_UNKNOWN_STRUCT__NA_238E85C: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SHOP_MENU_ITEMS_CONFIRM: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SHOP_MAIN_MENU_ITEMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SHOP_MAIN_MENU_ITEMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SHOP_MAIN_MENU_ITEMS_3: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY22_UNKNOWN_STRING_IDS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SHOP_WINDOW_PARAMS_3: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SHOP_WINDOW_PARAMS_4: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SHOP_WINDOW_PARAMS_5: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SHOP_WINDOW_PARAMS_6: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SHOP_WINDOW_PARAMS_7: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SHOP_WINDOW_PARAMS_8: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SHOP_WINDOW_PARAMS_9: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SHOP_WINDOW_PARAMS_10: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY22_RESERVED_SPACE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY22_UNKNOWN_POINTER__NA_238EC60: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY22_UNKNOWN_POINTER__NA_238EC64: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY22_UNKNOWN_POINTER__NA_238EC68: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY22_UNKNOWN_POINTER__NA_238EC6C: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY22_UNKNOWN_POINTER__NA_238EC70: Symbol[
        Optional[list[int]],
        Optional[int],
    ]


Overlay22Protocol = SectionProtocol[
    Overlay22FunctionsProtocol,
    Overlay22DataProtocol,
    Optional[int],
]


class Overlay23FunctionsProtocol(Protocol):

    pass


class Overlay23DataProtocol(Protocol):

    OVERLAY23_UNKNOWN_VALUE__NA_238D2E8: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY23_UNKNOWN_VALUE__NA_238D2EC: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY23_UNKNOWN_STRUCT__NA_238D2F0: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STORAGE_MENU_ITEMS_CONFIRM: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STORAGE_MAIN_MENU_ITEMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STORAGE_MAIN_MENU_ITEMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STORAGE_MAIN_MENU_ITEMS_3: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STORAGE_MAIN_MENU_ITEMS_4: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY23_UNKNOWN_STRING_IDS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STORAGE_WINDOW_PARAMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STORAGE_WINDOW_PARAMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STORAGE_WINDOW_PARAMS_3: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STORAGE_WINDOW_PARAMS_4: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STORAGE_WINDOW_PARAMS_5: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STORAGE_WINDOW_PARAMS_6: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STORAGE_WINDOW_PARAMS_7: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STORAGE_WINDOW_PARAMS_8: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY23_RESERVED_SPACE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY23_UNKNOWN_POINTER__NA_238D8A0: Symbol[
        Optional[list[int]],
        Optional[int],
    ]


Overlay23Protocol = SectionProtocol[
    Overlay23FunctionsProtocol,
    Overlay23DataProtocol,
    Optional[int],
]


class Overlay24FunctionsProtocol(Protocol):

    pass


class Overlay24DataProtocol(Protocol):

    OVERLAY24_UNKNOWN_STRUCT__NA_238C508: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY24_UNKNOWN_STRUCT__NA_238C514: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DAYCARE_MENU_ITEMS_CONFIRM: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DAYCARE_MAIN_MENU_ITEMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY24_UNKNOWN_STRING_IDS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DAYCARE_WINDOW_PARAMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DAYCARE_WINDOW_PARAMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DAYCARE_WINDOW_PARAMS_3: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DAYCARE_WINDOW_PARAMS_4: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DAYCARE_WINDOW_PARAMS_5: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY24_RESERVED_SPACE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY24_UNKNOWN_POINTER__NA_238C600: Symbol[
        Optional[list[int]],
        Optional[int],
    ]


Overlay24Protocol = SectionProtocol[
    Overlay24FunctionsProtocol,
    Overlay24DataProtocol,
    Optional[int],
]


class Overlay25FunctionsProtocol(Protocol):

    pass


class Overlay25DataProtocol(Protocol):

    OVERLAY25_UNKNOWN_STRUCT__NA_238B498: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    APPRAISAL_WINDOW_PARAMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    APPRAISAL_MENU_ITEMS_CONFIRM: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    APPRAISAL_MAIN_MENU_ITEMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    APPRAISAL_SUBMENU_ITEMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY25_UNKNOWN_STRING_IDS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    APPRAISAL_WINDOW_PARAMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    APPRAISAL_WINDOW_PARAMS_3: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    APPRAISAL_WINDOW_PARAMS_4: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    APPRAISAL_WINDOW_PARAMS_5: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    APPRAISAL_WINDOW_PARAMS_6: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    APPRAISAL_WINDOW_PARAMS_7: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    APPRAISAL_WINDOW_PARAMS_8: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY25_RESERVED_SPACE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY25_UNKNOWN_POINTER__NA_238B5E0: Symbol[
        Optional[list[int]],
        Optional[int],
    ]


Overlay25Protocol = SectionProtocol[
    Overlay25FunctionsProtocol,
    Overlay25DataProtocol,
    Optional[int],
]


class Overlay26FunctionsProtocol(Protocol):

    pass


class Overlay26DataProtocol(Protocol):

    OVERLAY26_UNKNOWN_TABLE__NA_238AE20: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY26_RESERVED_SPACE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY26_UNKNOWN_POINTER__NA_238AF60: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY26_UNKNOWN_POINTER__NA_238AF64: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY26_UNKNOWN_POINTER__NA_238AF68: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY26_UNKNOWN_POINTER__NA_238AF6C: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY26_UNKNOWN_POINTER5__NA_238AF70: Symbol[
        Optional[list[int]],
        Optional[int],
    ]


Overlay26Protocol = SectionProtocol[
    Overlay26FunctionsProtocol,
    Overlay26DataProtocol,
    Optional[int],
]


class Overlay27FunctionsProtocol(Protocol):

    pass


class Overlay27DataProtocol(Protocol):

    OVERLAY27_UNKNOWN_VALUE__NA_238C948: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY27_UNKNOWN_VALUE__NA_238C94C: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY27_UNKNOWN_STRUCT__NA_238C950: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DISCARD_ITEMS_MENU_ITEMS_CONFIRM: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DISCARD_ITEMS_SUBMENU_ITEMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DISCARD_ITEMS_SUBMENU_ITEMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DISCARD_ITEMS_MAIN_MENU_ITEMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY27_UNKNOWN_STRING_IDS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DISCARD_WINDOW_PARAMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DISCARD_WINDOW_PARAMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DISCARD_WINDOW_PARAMS_3: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DISCARD_WINDOW_PARAMS_4: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DISCARD_WINDOW_PARAMS_5: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DISCARD_WINDOW_PARAMS_6: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DISCARD_WINDOW_PARAMS_7: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DISCARD_WINDOW_PARAMS_8: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY27_RESERVED_SPACE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY27_UNKNOWN_POINTER__NA_238CE80: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY27_UNKNOWN_POINTER__NA_238CE84: Symbol[
        Optional[list[int]],
        Optional[int],
    ]


Overlay27Protocol = SectionProtocol[
    Overlay27FunctionsProtocol,
    Overlay27DataProtocol,
    Optional[int],
]


class Overlay28FunctionsProtocol(Protocol):

    pass


class Overlay28DataProtocol(Protocol):

    pass


Overlay28Protocol = SectionProtocol[
    Overlay28FunctionsProtocol,
    Overlay28DataProtocol,
    Optional[int],
]


class Overlay29FunctionsProtocol(Protocol):

    GetWeatherColorTable: Symbol[
        Optional[list[int]],
        None,
    ]

    DungeonAlloc: Symbol[
        Optional[list[int]],
        None,
    ]

    GetDungeonPtrMaster: Symbol[
        Optional[list[int]],
        None,
    ]

    DungeonZInit: Symbol[
        Optional[list[int]],
        None,
    ]

    DungeonFree: Symbol[
        Optional[list[int]],
        None,
    ]

    RunDungeon: Symbol[
        Optional[list[int]],
        None,
    ]

    EntityIsValid: Symbol[
        Optional[list[int]],
        None,
    ]

    GetFloorType: Symbol[
        Optional[list[int]],
        None,
    ]

    TryForcedLoss: Symbol[
        Optional[list[int]],
        None,
    ]

    IsBossFight: Symbol[
        Optional[list[int]],
        None,
    ]

    IsCurrentFixedRoomBossFight: Symbol[
        Optional[list[int]],
        None,
    ]

    IsMarowakTrainingMaze: Symbol[
        Optional[list[int]],
        None,
    ]

    FixedRoomIsSubstituteRoom: Symbol[
        Optional[list[int]],
        None,
    ]

    StoryRestrictionsEnabled: Symbol[
        Optional[list[int]],
        None,
    ]

    GetScenarioBalanceVeneer: Symbol[
        Optional[list[int]],
        None,
    ]

    FadeToBlack: Symbol[
        Optional[list[int]],
        None,
    ]

    CheckTouchscreenArea: Symbol[
        Optional[list[int]],
        None,
    ]

    GetTrapInfo: Symbol[
        Optional[list[int]],
        None,
    ]

    GetItemInfo: Symbol[
        Optional[list[int]],
        None,
    ]

    GetTileAtEntity: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateEntityPixelPos: Symbol[
        Optional[list[int]],
        None,
    ]

    SetEntityPixelPosXY: Symbol[
        Optional[list[int]],
        None,
    ]

    IncrementEntityPixelPosXY: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateEnemyEntity: Symbol[
        Optional[list[int]],
        None,
    ]

    SpawnTrap: Symbol[
        Optional[list[int]],
        None,
    ]

    SpawnItemEntity: Symbol[
        Optional[list[int]],
        None,
    ]

    ShouldMinimapDisplayEntity: Symbol[
        Optional[list[int]],
        None,
    ]

    ShouldDisplayEntity: Symbol[
        Optional[list[int]],
        None,
    ]

    ShouldDisplayEntityWrapper: Symbol[
        Optional[list[int]],
        None,
    ]

    CanSeeTarget: Symbol[
        Optional[list[int]],
        None,
    ]

    CanTargetEntity: Symbol[
        Optional[list[int]],
        None,
    ]

    CanTargetPosition: Symbol[
        Optional[list[int]],
        None,
    ]

    PopulateActiveMonsterPtrs: Symbol[
        Optional[list[int]],
        None,
    ]

    GetTeamMemberIndex: Symbol[
        Optional[list[int]],
        None,
    ]

    SubstitutePlaceholderStringTags: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateMapSurveyorFlag: Symbol[
        Optional[list[int]],
        None,
    ]

    PointCameraToMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateCamera: Symbol[
        Optional[list[int]],
        None,
    ]

    ItemIsActive: Symbol[
        Optional[list[int]],
        None,
    ]

    GetVisibilityRange: Symbol[
        Optional[list[int]],
        None,
    ]

    RevealWholeFloor: Symbol[
        Optional[list[int]],
        None,
    ]

    PlayEffectAnimationEntity: Symbol[
        Optional[list[int]],
        None,
    ]

    PlayEffectAnimationPos: Symbol[
        Optional[list[int]],
        None,
    ]

    PlayEffectAnimationPixelPos: Symbol[
        Optional[list[int]],
        None,
    ]

    AnimationDelayOrSomething: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateStatusIconFlags: Symbol[
        Optional[list[int]],
        None,
    ]

    PlayEffectAnimation0x171Full: Symbol[
        Optional[list[int]],
        None,
    ]

    PlayEffectAnimation0x171: Symbol[
        Optional[list[int]],
        None,
    ]

    ShowPpRestoreEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ShouldDisplayEntityAdvanced: Symbol[
        Optional[list[int]],
        None,
    ]

    PlayEffectAnimation0x1A9: Symbol[
        Optional[list[int]],
        None,
    ]

    PlayEffectAnimation0x18E: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadMappaFileAttributes: Symbol[
        Optional[list[int]],
        None,
    ]

    GetItemIdToSpawn: Symbol[
        Optional[list[int]],
        None,
    ]

    CopySpawnEntriesMaster: Symbol[
        Optional[list[int]],
        None,
    ]

    MonsterSpawnListPartialCopy: Symbol[
        Optional[list[int]],
        None,
    ]

    IsOnMonsterSpawnList: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMonsterIdToSpawn: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMonsterLevelToSpawn: Symbol[
        Optional[list[int]],
        None,
    ]

    AllocTopScreenStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    FreeTopScreenStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    InitializeTeamStats: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateTeamStatsWrapper: Symbol[
        Optional[list[int]],
        None,
    ]

    FreeTeamStatsWrapper: Symbol[
        Optional[list[int]],
        None,
    ]

    AssignTopScreenHandlers: Symbol[
        Optional[list[int]],
        None,
    ]

    HandleTopScreenFades: Symbol[
        Optional[list[int]],
        None,
    ]

    FreeTopScreen: Symbol[
        Optional[list[int]],
        None,
    ]

    GetDirectionTowardsPosition: Symbol[
        Optional[list[int]],
        None,
    ]

    GetChebyshevDistance: Symbol[
        Optional[list[int]],
        None,
    ]

    IsPositionActuallyInSight: Symbol[
        Optional[list[int]],
        None,
    ]

    IsPositionInSight: Symbol[
        Optional[list[int]],
        None,
    ]

    GetLeader: Symbol[
        Optional[list[int]],
        None,
    ]

    GetLeaderMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    GetRandomTile: Symbol[
        Optional[list[int]],
        None,
    ]

    FindNearbyUnoccupiedTile: Symbol[
        Optional[list[int]],
        None,
    ]

    FindClosestUnoccupiedTileWithin2: Symbol[
        Optional[list[int]],
        None,
    ]

    FindFarthestUnoccupiedTileWithin2: Symbol[
        Optional[list[int]],
        None,
    ]

    FindUnoccupiedTileWithin3: Symbol[
        Optional[list[int]],
        None,
    ]

    TickStatusTurnCounter: Symbol[
        Optional[list[int]],
        None,
    ]

    AdvanceFrame: Symbol[
        Optional[list[int]],
        None,
    ]

    DisplayAnimatedNumbers: Symbol[
        Optional[list[int]],
        None,
    ]

    SetDungeonRngPreseed23Bit: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateDungeonRngSeed: Symbol[
        Optional[list[int]],
        None,
    ]

    GetDungeonRngPreseed: Symbol[
        Optional[list[int]],
        None,
    ]

    SetDungeonRngPreseed: Symbol[
        Optional[list[int]],
        None,
    ]

    InitDungeonRng: Symbol[
        Optional[list[int]],
        None,
    ]

    DungeonRand16Bit: Symbol[
        Optional[list[int]],
        None,
    ]

    DungeonRandInt: Symbol[
        Optional[list[int]],
        None,
    ]

    DungeonRandRange: Symbol[
        Optional[list[int]],
        None,
    ]

    DungeonRandOutcome: Symbol[
        Optional[list[int]],
        None,
    ]

    CalcStatusDuration: Symbol[
        Optional[list[int]],
        None,
    ]

    DungeonRngUnsetSecondary: Symbol[
        Optional[list[int]],
        None,
    ]

    DungeonRngSetSecondary: Symbol[
        Optional[list[int]],
        None,
    ]

    DungeonRngSetPrimary: Symbol[
        Optional[list[int]],
        None,
    ]

    MusicTableIdxToMusicId: Symbol[
        Optional[list[int]],
        None,
    ]

    ChangeDungeonMusic: Symbol[
        Optional[list[int]],
        None,
    ]

    TrySwitchPlace: Symbol[
        Optional[list[int]],
        None,
    ]

    SetLeaderActionFields: Symbol[
        Optional[list[int]],
        None,
    ]

    ClearMonsterActionFields: Symbol[
        Optional[list[int]],
        None,
    ]

    SetMonsterActionFields: Symbol[
        Optional[list[int]],
        None,
    ]

    SetActionPassTurnOrWalk: Symbol[
        Optional[list[int]],
        None,
    ]

    GetItemToUseByIndex: Symbol[
        Optional[list[int]],
        None,
    ]

    GetItemToUse: Symbol[
        Optional[list[int]],
        None,
    ]

    GetItemAction: Symbol[
        Optional[list[int]],
        None,
    ]

    RemoveUsedItem: Symbol[
        Optional[list[int]],
        None,
    ]

    AddDungeonSubMenuOption: Symbol[
        Optional[list[int]],
        None,
    ]

    DisableDungeonSubMenuOption: Symbol[
        Optional[list[int]],
        None,
    ]

    SetActionRegularAttack: Symbol[
        Optional[list[int]],
        None,
    ]

    SetActionUseMovePlayer: Symbol[
        Optional[list[int]],
        None,
    ]

    SetActionUseMoveAi: Symbol[
        Optional[list[int]],
        None,
    ]

    RunFractionalTurn: Symbol[
        Optional[list[int]],
        None,
    ]

    RunLeaderTurn: Symbol[
        Optional[list[int]],
        None,
    ]

    TrySpawnMonsterAndActivatePlusMinus: Symbol[
        Optional[list[int]],
        None,
    ]

    IsFloorOver: Symbol[
        Optional[list[int]],
        None,
    ]

    DecrementWindCounter: Symbol[
        Optional[list[int]],
        None,
    ]

    IsDungeonEndReasonFailure: Symbol[
        Optional[list[int]],
        None,
    ]

    SetForcedLossReason: Symbol[
        Optional[list[int]],
        None,
    ]

    GetForcedLossReason: Symbol[
        Optional[list[int]],
        None,
    ]

    BindTrapToTile: Symbol[
        Optional[list[int]],
        None,
    ]

    AreLateGameTrapsEnabledWrapper: Symbol[
        Optional[list[int]],
        None,
    ]

    SpawnEnemyTrapAtPos: Symbol[
        Optional[list[int]],
        None,
    ]

    PrepareTrapperTrap: Symbol[
        Optional[list[int]],
        None,
    ]

    TrySpawnTrap: Symbol[
        Optional[list[int]],
        None,
    ]

    TrySpawnTrapperTrap: Symbol[
        Optional[list[int]],
        None,
    ]

    TryRemoveTrap: Symbol[
        Optional[list[int]],
        None,
    ]

    TryTriggerTrap: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyMudTrapEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyStickyTrapEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyGrimyTrapEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyPitfallTrapEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplySummonTrapEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyPpZeroTrapEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyPokemonTrapEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyTripTrapEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyStealthRockTrapEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyToxicSpikesTrapEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyRandomTrapEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyGrudgeTrapEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyTrapEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    RevealTrapsNearby: Symbol[
        Optional[list[int]],
        None,
    ]

    ShouldRunMonsterAi: Symbol[
        Optional[list[int]],
        None,
    ]

    DebugRecruitingEnabled: Symbol[
        Optional[list[int]],
        None,
    ]

    TryActivateIqBooster: Symbol[
        Optional[list[int]],
        None,
    ]

    IsSecretBazaarNpcBehavior: Symbol[
        Optional[list[int]],
        None,
    ]

    GetLeaderAction: Symbol[
        Optional[list[int]],
        None,
    ]

    GetEntityTouchscreenArea: Symbol[
        Optional[list[int]],
        None,
    ]

    SetLeaderAction: Symbol[
        Optional[list[int]],
        None,
    ]

    ShouldLeaderKeepRunning: Symbol[
        Optional[list[int]],
        None,
    ]

    CheckLeaderTile: Symbol[
        Optional[list[int]],
        None,
    ]

    ChangeLeader: Symbol[
        Optional[list[int]],
        None,
    ]

    UseSingleUseItemWrapper: Symbol[
        Optional[list[int]],
        None,
    ]

    UseSingleUseItem: Symbol[
        Optional[list[int]],
        None,
    ]

    UseThrowableItem: Symbol[
        Optional[list[int]],
        None,
    ]

    ResetDamageData: Symbol[
        Optional[list[int]],
        None,
    ]

    FreeLoadedAttackSpriteAndMore: Symbol[
        Optional[list[int]],
        None,
    ]

    SetAndLoadCurrentAttackAnimation: Symbol[
        Optional[list[int]],
        None,
    ]

    ClearLoadedAttackSprite: Symbol[
        Optional[list[int]],
        None,
    ]

    GetLoadedAttackSpriteId: Symbol[
        Optional[list[int]],
        None,
    ]

    DungeonGetTotalSpriteFileSize: Symbol[
        Optional[list[int]],
        None,
    ]

    DungeonGetSpriteIndex: Symbol[
        Optional[list[int]],
        None,
    ]

    JoinedAtRangeCheck2Veneer: Symbol[
        Optional[list[int]],
        None,
    ]

    FloorNumberIsEven: Symbol[
        Optional[list[int]],
        None,
    ]

    GetKecleonIdToSpawnByFloor: Symbol[
        Optional[list[int]],
        None,
    ]

    StoreSpriteFileIndexBothGenders: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadMonsterSpriteInner: Symbol[
        Optional[list[int]],
        None,
    ]

    SwapMonsterWanFileIndex: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadMonsterSprite: Symbol[
        Optional[list[int]],
        None,
    ]

    DeleteMonsterSpriteFile: Symbol[
        Optional[list[int]],
        None,
    ]

    DeleteAllMonsterSpriteFiles: Symbol[
        Optional[list[int]],
        None,
    ]

    EuFaintCheck: Symbol[
        Optional[list[int]],
        None,
    ]

    HandleFaint: Symbol[
        Optional[list[int]],
        None,
    ]

    MoveMonsterToPos: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateMonsterSummaryFromMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateAiTargetPos: Symbol[
        Optional[list[int]],
        None,
    ]

    SetMonsterTypeAndAbility: Symbol[
        Optional[list[int]],
        None,
    ]

    TryActivateSlowStart: Symbol[
        Optional[list[int]],
        None,
    ]

    TryActivateArtificialWeatherAbilities: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMonsterApparentId: Symbol[
        Optional[list[int]],
        None,
    ]

    TryActivateTraceAndColorChange: Symbol[
        Optional[list[int]],
        None,
    ]

    DefenderAbilityIsActive: Symbol[
        Optional[list[int]],
        None,
    ]

    IsMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    TryActivateConversion2: Symbol[
        Optional[list[int]],
        None,
    ]

    TryActivateTruant: Symbol[
        Optional[list[int]],
        None,
    ]

    TryPointCameraToMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    ReevaluateSnatchMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    GetRandomExplorerMazeMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    RestorePpAllMovesSetFlags: Symbol[
        Optional[list[int]],
        None,
    ]

    CheckTeamMemberIdxVeneer: Symbol[
        Optional[list[int]],
        None,
    ]

    IsMonsterIdInNormalRangeVeneer: Symbol[
        Optional[list[int]],
        None,
    ]

    BoostIQ: Symbol[
        Optional[list[int]],
        None,
    ]

    ShouldMonsterHeadToStairs: Symbol[
        Optional[list[int]],
        None,
    ]

    MewSpawnCheck: Symbol[
        Optional[list[int]],
        None,
    ]

    TryEndStatusWithAbility: Symbol[
        Optional[list[int]],
        None,
    ]

    ExclusiveItemEffectIsActive: Symbol[
        Optional[list[int]],
        None,
    ]

    GetTeamMemberWithIqSkill: Symbol[
        Optional[list[int]],
        None,
    ]

    TeamMemberHasEnabledIqSkill: Symbol[
        Optional[list[int]],
        None,
    ]

    TeamLeaderIqSkillIsEnabled: Symbol[
        Optional[list[int]],
        None,
    ]

    CountMovesOutOfPp: Symbol[
        Optional[list[int]],
        None,
    ]

    HasSuperEffectiveMoveAgainstUser: Symbol[
        Optional[list[int]],
        None,
    ]

    TryEatItem: Symbol[
        Optional[list[int]],
        None,
    ]

    SetDecoyAiTracker: Symbol[
        Optional[list[int]],
        None,
    ]

    CheckSpawnThreshold: Symbol[
        Optional[list[int]],
        None,
    ]

    HasLowHealth: Symbol[
        Optional[list[int]],
        None,
    ]

    AreEntitiesAdjacent: Symbol[
        Optional[list[int]],
        None,
    ]

    IsSpecialStoryAlly: Symbol[
        Optional[list[int]],
        None,
    ]

    IsExperienceLocked: Symbol[
        Optional[list[int]],
        None,
    ]

    InitOtherMonsterData: Symbol[
        Optional[list[int]],
        None,
    ]

    InitEnemySpawnStats: Symbol[
        Optional[list[int]],
        None,
    ]

    InitEnemyStatsAndMoves: Symbol[
        Optional[list[int]],
        None,
    ]

    SpawnTeam: Symbol[
        Optional[list[int]],
        None,
    ]

    SpawnInitialMonsters: Symbol[
        Optional[list[int]],
        None,
    ]

    SpawnMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    InitTeamMember: Symbol[
        Optional[list[int]],
        None,
    ]

    InitMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    SubInitMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    MarkShopkeeperSpawn: Symbol[
        Optional[list[int]],
        None,
    ]

    SpawnShopkeepers: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMaxHpAtLevel: Symbol[
        Optional[list[int]],
        None,
    ]

    GetOffensiveStatAtLevel: Symbol[
        Optional[list[int]],
        None,
    ]

    GetDefensiveStatAtLevel: Symbol[
        Optional[list[int]],
        None,
    ]

    GetOutlawSpawnData: Symbol[
        Optional[list[int]],
        None,
    ]

    ExecuteMonsterAction: Symbol[
        Optional[list[int]],
        None,
    ]

    TryActivateFlashFireOnAllMonsters: Symbol[
        Optional[list[int]],
        None,
    ]

    HasStatusThatPreventsActing: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMobilityTypeCheckSlip: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMobilityTypeCheckSlipAndFloating: Symbol[
        Optional[list[int]],
        None,
    ]

    IsInvalidSpawnTile: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMobilityTypeAfterIqSkills: Symbol[
        Optional[list[int]],
        None,
    ]

    CannotStandOnTile: Symbol[
        Optional[list[int]],
        None,
    ]

    CalcSpeedStage: Symbol[
        Optional[list[int]],
        None,
    ]

    CalcSpeedStageWrapper: Symbol[
        Optional[list[int]],
        None,
    ]

    GetNumberOfAttacks: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMonsterDisplayNameType: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMonsterName: Symbol[
        Optional[list[int]],
        None,
    ]

    SprintfStatic: Symbol[
        Optional[list[int]],
        None,
    ]

    IsMonsterDrowsy: Symbol[
        Optional[list[int]],
        None,
    ]

    MonsterHasNonvolatileNonsleepStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    MonsterHasImmobilizingStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    MonsterHasAttackInterferingStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    MonsterHasSkillInterferingStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    MonsterHasLeechSeedStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    MonsterHasWhifferStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    IsMonsterVisuallyImpaired: Symbol[
        Optional[list[int]],
        None,
    ]

    IsMonsterMuzzled: Symbol[
        Optional[list[int]],
        None,
    ]

    MonsterHasMiracleEyeStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    MonsterHasNegativeStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    IsMonsterSleeping: Symbol[
        Optional[list[int]],
        None,
    ]

    CheckVariousStatuses2: Symbol[
        Optional[list[int]],
        None,
    ]

    CheckVariousConditions: Symbol[
        Optional[list[int]],
        None,
    ]

    CheckVariousStatuses: Symbol[
        Optional[list[int]],
        None,
    ]

    CanMonsterMoveInDirection: Symbol[
        Optional[list[int]],
        None,
    ]

    GetDirectionalMobilityType: Symbol[
        Optional[list[int]],
        None,
    ]

    IsMonsterCornered: Symbol[
        Optional[list[int]],
        None,
    ]

    CanAttackInDirection: Symbol[
        Optional[list[int]],
        None,
    ]

    CanAiMonsterMoveInDirection: Symbol[
        Optional[list[int]],
        None,
    ]

    ShouldMonsterRunAway: Symbol[
        Optional[list[int]],
        None,
    ]

    ShouldMonsterRunAwayVariation: Symbol[
        Optional[list[int]],
        None,
    ]

    GetTreatmentBetweenMonsters: Symbol[
        Optional[list[int]],
        None,
    ]

    SafeguardIsActive: Symbol[
        Optional[list[int]],
        None,
    ]

    LeafGuardIsActive: Symbol[
        Optional[list[int]],
        None,
    ]

    IsProtectedFromStatDrops: Symbol[
        Optional[list[int]],
        None,
    ]

    NoGastroAcidStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    AbilityIsActive: Symbol[
        Optional[list[int]],
        None,
    ]

    AbilityIsActiveVeneer: Symbol[
        Optional[list[int]],
        None,
    ]

    OtherMonsterAbilityIsActive: Symbol[
        Optional[list[int]],
        None,
    ]

    LevitateIsActive: Symbol[
        Optional[list[int]],
        None,
    ]

    MonsterIsType: Symbol[
        Optional[list[int]],
        None,
    ]

    IsTypeAffectedByGravity: Symbol[
        Optional[list[int]],
        None,
    ]

    HasTypeAffectedByGravity: Symbol[
        Optional[list[int]],
        None,
    ]

    CanSeeInvisibleMonsters: Symbol[
        Optional[list[int]],
        None,
    ]

    IsTacticSet: Symbol[
        Optional[list[int]],
        None,
    ]

    HasDropeyeStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    IqSkillIsEnabled: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateIqSkills: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMoveTypeForMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMovePower: Symbol[
        Optional[list[int]],
        None,
    ]

    MonsterCanThrowItems: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateStateFlags: Symbol[
        Optional[list[int]],
        None,
    ]

    IsProtectedFromNegativeStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    AddExpSpecial: Symbol[
        Optional[list[int]],
        None,
    ]

    EnemyEvolution: Symbol[
        Optional[list[int]],
        None,
    ]

    LevelUpItemEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    TryDecreaseLevel: Symbol[
        Optional[list[int]],
        None,
    ]

    LevelUp: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMonsterMoves: Symbol[
        Optional[list[int]],
        None,
    ]

    EvolveMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    ChangeMonsterAnimation: Symbol[
        Optional[list[int]],
        None,
    ]

    GetIdleAnimationId: Symbol[
        Optional[list[int]],
        None,
    ]

    DetermineAllMonsterShadow: Symbol[
        Optional[list[int]],
        None,
    ]

    DetermineMonsterShadow: Symbol[
        Optional[list[int]],
        None,
    ]

    DisplayActions: Symbol[
        Optional[list[int]],
        None,
    ]

    CheckNonLeaderTile: Symbol[
        Optional[list[int]],
        None,
    ]

    EndNegativeStatusCondition: Symbol[
        Optional[list[int]],
        None,
    ]

    EndNegativeStatusConditionWrapper: Symbol[
        Optional[list[int]],
        None,
    ]

    TransferNegativeStatusCondition: Symbol[
        Optional[list[int]],
        None,
    ]

    EndSleepClassStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    EndBurnClassStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    EndFrozenClassStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    EndCringeClassStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    EndReflectClassStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryRemoveSnatchedMonsterFromDungeonStruct: Symbol[
        Optional[list[int]],
        None,
    ]

    EndCurseClassStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    EndLeechSeedClassStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    EndSureShotClassStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    EndInvisibleClassStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    EndBlinkerClassStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    EndMuzzledStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    EndMiracleEyeStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    EndMagnetRiseStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TransferNegativeBlinkerClassStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    EndFrozenStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    EndProtectStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryRestoreRoostTyping: Symbol[
        Optional[list[int]],
        None,
    ]

    TryTriggerMonsterHouse: Symbol[
        Optional[list[int]],
        None,
    ]

    ShouldMonsterFollowLeader: Symbol[
        Optional[list[int]],
        None,
    ]

    RunMonsterAi: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyDamageAndEffects: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyDamage: Symbol[
        Optional[list[int]],
        None,
    ]

    AftermathCheck: Symbol[
        Optional[list[int]],
        None,
    ]

    GetTypeMatchupBothTypes: Symbol[
        Optional[list[int]],
        None,
    ]

    ScrappyShouldActivate: Symbol[
        Optional[list[int]],
        None,
    ]

    IsTypeIneffectiveAgainstGhost: Symbol[
        Optional[list[int]],
        None,
    ]

    GhostImmunityIsActive: Symbol[
        Optional[list[int]],
        None,
    ]

    GetTypeMatchup: Symbol[
        Optional[list[int]],
        None,
    ]

    CalcTypeBasedDamageEffects: Symbol[
        Optional[list[int]],
        None,
    ]

    CalcDamage: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyDamageAndEffectsWrapper: Symbol[
        Optional[list[int]],
        None,
    ]

    CalcRecoilDamageFixed: Symbol[
        Optional[list[int]],
        None,
    ]

    CalcDamageFixed: Symbol[
        Optional[list[int]],
        None,
    ]

    CalcDamageFixedNoCategory: Symbol[
        Optional[list[int]],
        None,
    ]

    CalcDamageFixedWrapper: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateShopkeeperModeAfterAttack: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateShopkeeperModeAfterTrap: Symbol[
        Optional[list[int]],
        None,
    ]

    ResetDamageCalcDiagnostics: Symbol[
        Optional[list[int]],
        None,
    ]

    SpecificRecruitCheck: Symbol[
        Optional[list[int]],
        None,
    ]

    RecruitCheck: Symbol[
        Optional[list[int]],
        None,
    ]

    TryRecruit: Symbol[
        Optional[list[int]],
        None,
    ]

    TrySpawnMonsterAndTickSpawnCounter: Symbol[
        Optional[list[int]],
        None,
    ]

    AiDecideUseItem: Symbol[
        Optional[list[int]],
        None,
    ]

    GetPossibleAiThrownItemDirections: Symbol[
        Optional[list[int]],
        None,
    ]

    GetPossibleAiArcItemTargets: Symbol[
        Optional[list[int]],
        None,
    ]

    TryNonLeaderItemPickUp: Symbol[
        Optional[list[int]],
        None,
    ]

    GetExclusiveItemWithEffectFromBag: Symbol[
        Optional[list[int]],
        None,
    ]

    AuraBowIsActive: Symbol[
        Optional[list[int]],
        None,
    ]

    ExclusiveItemOffenseBoost: Symbol[
        Optional[list[int]],
        None,
    ]

    ExclusiveItemDefenseBoost: Symbol[
        Optional[list[int]],
        None,
    ]

    TeamMemberHasItemActive: Symbol[
        Optional[list[int]],
        None,
    ]

    TeamMemberHasExclusiveItemEffectActive: Symbol[
        Optional[list[int]],
        None,
    ]

    TrySpawnEnemyItemDrop: Symbol[
        Optional[list[int]],
        None,
    ]

    TickNoSlipCap: Symbol[
        Optional[list[int]],
        None,
    ]

    TickStatusAndHealthRegen: Symbol[
        Optional[list[int]],
        None,
    ]

    InflictSleepStatusSingle: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictSleepStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    IsProtectedFromSleepClassStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictNightmareStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictNappingStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictYawningStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictSleeplessStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictPausedStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictInfatuatedStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictBurnStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictBurnStatusWholeTeam: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictPoisonedStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictBadlyPoisonedStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictFrozenStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictConstrictionStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictShadowHoldStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictIngrainStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictWrappedStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    FreeOtherWrappedMonsters: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictPetrifiedStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    LowerOffensiveStat: Symbol[
        Optional[list[int]],
        None,
    ]

    LowerDefensiveStat: Symbol[
        Optional[list[int]],
        None,
    ]

    BoostOffensiveStat: Symbol[
        Optional[list[int]],
        None,
    ]

    BoostDefensiveStat: Symbol[
        Optional[list[int]],
        None,
    ]

    FlashFireShouldActivate: Symbol[
        Optional[list[int]],
        None,
    ]

    ActivateFlashFire: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyOffensiveStatMultiplier: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyDefensiveStatMultiplier: Symbol[
        Optional[list[int]],
        None,
    ]

    BoostHitChanceStat: Symbol[
        Optional[list[int]],
        None,
    ]

    LowerHitChanceStat: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictCringeStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictParalysisStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    BoostSpeed: Symbol[
        Optional[list[int]],
        None,
    ]

    BoostSpeedOneStage: Symbol[
        Optional[list[int]],
        None,
    ]

    LowerSpeed: Symbol[
        Optional[list[int]],
        None,
    ]

    TrySealMove: Symbol[
        Optional[list[int]],
        None,
    ]

    BoostOrLowerSpeed: Symbol[
        Optional[list[int]],
        None,
    ]

    ResetHitChanceStat: Symbol[
        Optional[list[int]],
        None,
    ]

    ExclusiveItemEffectIsActiveWithLogging: Symbol[
        Optional[list[int]],
        None,
    ]

    TryActivateQuickFeet: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictTerrifiedStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictGrudgeStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictConfusedStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictCoweringStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryRestoreHp: Symbol[
        Optional[list[int]],
        None,
    ]

    TryIncreaseHp: Symbol[
        Optional[list[int]],
        None,
    ]

    RevealItems: Symbol[
        Optional[list[int]],
        None,
    ]

    RevealStairs: Symbol[
        Optional[list[int]],
        None,
    ]

    RevealEnemies: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictLeechSeedStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictDestinyBondStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictSureShotStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictWhifferStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictSetDamageStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictFocusEnergyStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictDecoyStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictCurseStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictSnatchStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictTauntStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictStockpileStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictInvisibleStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictPerishSongStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictEncoreStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryDecreaseBelly: Symbol[
        Optional[list[int]],
        None,
    ]

    TryIncreaseBelly: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictMuzzledStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryTransform: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictMobileStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictExposedStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryActivateIdentifyCondition: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictBlinkerStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    IsBlinded: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictCrossEyedStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictEyedropStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictSlipStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictDropeyeStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    RestoreAllMovePP: Symbol[
        Optional[list[int]],
        None,
    ]

    RestoreOneMovePP: Symbol[
        Optional[list[int]],
        None,
    ]

    RestoreRandomMovePP: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyProteinEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyCalciumEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyIronEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyZincEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictLongTossStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictPierceStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictGastroAcidStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    SetAquaRingHealingCountdownTo4: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyAquaRingHealing: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictAquaRingStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictLuckyChantStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictHealBlockStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    MonsterHasEmbargoStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    LogItemBlockedByEmbargo: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictEmbargoStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictMiracleEyeStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictMagnetRiseStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    IsFloating: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictSafeguardStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictMistStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictWishStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictMagicCoatStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictLightScreenStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictReflectStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictProtectStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictMirrorCoatStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictEndureStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictMirrorMoveStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictConversion2Status: Symbol[
        Optional[list[int]],
        None,
    ]

    TryInflictVitalThrowStatus: Symbol[
        Optional[list[int]],
        None,
    ]

    TryResetStatChanges: Symbol[
        Optional[list[int]],
        None,
    ]

    MirrorMoveIsActive: Symbol[
        Optional[list[int]],
        None,
    ]

    MistIsActive: Symbol[
        Optional[list[int]],
        None,
    ]

    Conversion2IsActive: Symbol[
        Optional[list[int]],
        None,
    ]

    AiConsiderMove: Symbol[
        Optional[list[int]],
        None,
    ]

    TryAddTargetToAiTargetList: Symbol[
        Optional[list[int]],
        None,
    ]

    IsAiTargetEligible: Symbol[
        Optional[list[int]],
        None,
    ]

    IsTargetInRange: Symbol[
        Optional[list[int]],
        None,
    ]

    ShouldUsePp: Symbol[
        Optional[list[int]],
        None,
    ]

    GetEntityMoveTargetAndRange: Symbol[
        Optional[list[int]],
        None,
    ]

    GetEntityNaturalGiftInfo: Symbol[
        Optional[list[int]],
        None,
    ]

    GetEntityWeatherBallType: Symbol[
        Optional[list[int]],
        None,
    ]

    ActivateMotorDrive: Symbol[
        Optional[list[int]],
        None,
    ]

    TryActivateFrisk: Symbol[
        Optional[list[int]],
        None,
    ]

    TryActivateBadDreams: Symbol[
        Optional[list[int]],
        None,
    ]

    ActivateStench: Symbol[
        Optional[list[int]],
        None,
    ]

    TryActivateSteadfast: Symbol[
        Optional[list[int]],
        None,
    ]

    IsInSpawnList: Symbol[
        Optional[list[int]],
        None,
    ]

    ChangeShayminForme: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyItemEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyCheriBerryEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyPechaBerryEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyRawstBerryEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyHungerSeedEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyVileSeedEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyViolentSeedEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyGinsengEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyBlastSeedEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyGummiBoostsDungeonMode: Symbol[
        Optional[list[int]],
        None,
    ]

    CanMonsterUseItem: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyGrimyFoodEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyMixElixirEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyDoughSeedEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyViaSeedEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyGravelyrockEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyGonePebbleEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyGracideaEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    GetAiUseItemProbability: Symbol[
        Optional[list[int]],
        None,
    ]

    IsAdjacentToEnemy: Symbol[
        Optional[list[int]],
        None,
    ]

    ShouldTryEatItem: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMaxPpWrapper: Symbol[
        Optional[list[int]],
        None,
    ]

    MoveIsNotPhysical: Symbol[
        Optional[list[int]],
        None,
    ]

    CategoryIsNotPhysical: Symbol[
        Optional[list[int]],
        None,
    ]

    TryDrought: Symbol[
        Optional[list[int]],
        None,
    ]

    TryPounce: Symbol[
        Optional[list[int]],
        None,
    ]

    TryBlowAway: Symbol[
        Optional[list[int]],
        None,
    ]

    TryExplosion: Symbol[
        Optional[list[int]],
        None,
    ]

    TryAftermathExplosion: Symbol[
        Optional[list[int]],
        None,
    ]

    TryWarp: Symbol[
        Optional[list[int]],
        None,
    ]

    EnsureCanStandCurrentTile: Symbol[
        Optional[list[int]],
        None,
    ]

    TryActivateNondamagingDefenderAbility: Symbol[
        Optional[list[int]],
        None,
    ]

    TryActivateNondamagingDefenderExclusiveItem: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMoveRangeDistance: Symbol[
        Optional[list[int]],
        None,
    ]

    MoveHitCheck: Symbol[
        Optional[list[int]],
        None,
    ]

    IsHyperBeamVariant: Symbol[
        Optional[list[int]],
        None,
    ]

    IsChargingTwoTurnMove: Symbol[
        Optional[list[int]],
        None,
    ]

    IsChargingAnyTwoTurnMove: Symbol[
        Optional[list[int]],
        None,
    ]

    HasMaxGinsengBoost99: Symbol[
        Optional[list[int]],
        None,
    ]

    TwoTurnMoveForcedMiss: Symbol[
        Optional[list[int]],
        None,
    ]

    DungeonRandOutcomeUserTargetInteraction: Symbol[
        Optional[list[int]],
        None,
    ]

    DungeonRandOutcomeUserAction: Symbol[
        Optional[list[int]],
        None,
    ]

    CanAiUseMove: Symbol[
        Optional[list[int]],
        None,
    ]

    CanMonsterUseMove: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateMovePp: Symbol[
        Optional[list[int]],
        None,
    ]

    GetDamageSourceWrapper: Symbol[
        Optional[list[int]],
        None,
    ]

    LowerSshort: Symbol[
        Optional[list[int]],
        None,
    ]

    PlayMoveAnimation: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMoveAnimationId: Symbol[
        Optional[list[int]],
        None,
    ]

    ShouldMovePlayAlternativeAnimation: Symbol[
        Optional[list[int]],
        None,
    ]

    ExecuteMoveEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    DoMoveDamageInlined: Symbol[
        Optional[list[int]],
        None,
    ]

    DealDamage: Symbol[
        Optional[list[int]],
        None,
    ]

    DealDamageWithTypeAndPowerBoost: Symbol[
        Optional[list[int]],
        None,
    ]

    DealDamageProjectile: Symbol[
        Optional[list[int]],
        None,
    ]

    DealDamageWithType: Symbol[
        Optional[list[int]],
        None,
    ]

    PerformDamageSequence: Symbol[
        Optional[list[int]],
        None,
    ]

    CanHitWithRegularAttack: Symbol[
        Optional[list[int]],
        None,
    ]

    StatusCheckerCheck: Symbol[
        Optional[list[int]],
        None,
    ]

    GetApparentWeather: Symbol[
        Optional[list[int]],
        None,
    ]

    TryWeatherFormChange: Symbol[
        Optional[list[int]],
        None,
    ]

    ActivateSportCondition: Symbol[
        Optional[list[int]],
        None,
    ]

    TryActivateWeather: Symbol[
        Optional[list[int]],
        None,
    ]

    DigitCount: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadTextureUi: Symbol[
        Optional[list[int]],
        None,
    ]

    DisplayNumberTextureUi: Symbol[
        Optional[list[int]],
        None,
    ]

    DisplayCharTextureUi: Symbol[
        Optional[list[int]],
        None,
    ]

    DisplayUi: Symbol[
        Optional[list[int]],
        None,
    ]

    GetTile: Symbol[
        Optional[list[int]],
        None,
    ]

    GetTileSafe: Symbol[
        Optional[list[int]],
        None,
    ]

    IsFullFloorFixedRoom: Symbol[
        Optional[list[int]],
        None,
    ]

    IsCurrentTilesetBackground: Symbol[
        Optional[list[int]],
        None,
    ]

    TrySpawnGoldenChamber: Symbol[
        Optional[list[int]],
        None,
    ]

    CountItemsOnFloorForAcuteSniffer: Symbol[
        Optional[list[int]],
        None,
    ]

    GetStairsSpawnPosition: Symbol[
        Optional[list[int]],
        None,
    ]

    PositionIsOnStairs: Symbol[
        Optional[list[int]],
        None,
    ]

    GetStairsRoom: Symbol[
        Optional[list[int]],
        None,
    ]

    GetDefaultTileTextureId: Symbol[
        Optional[list[int]],
        None,
    ]

    DetermineAllTilesWalkableNeighbors: Symbol[
        Optional[list[int]],
        None,
    ]

    DetermineTileWalkableNeighbors: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateTrapsVisibility: Symbol[
        Optional[list[int]],
        None,
    ]

    DrawTileGrid: Symbol[
        Optional[list[int]],
        None,
    ]

    HideTileGrid: Symbol[
        Optional[list[int]],
        None,
    ]

    DiscoverMinimap: Symbol[
        Optional[list[int]],
        None,
    ]

    PositionHasItem: Symbol[
        Optional[list[int]],
        None,
    ]

    PositionHasMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    TrySmashWall: Symbol[
        Optional[list[int]],
        None,
    ]

    IsWaterTileset: Symbol[
        Optional[list[int]],
        None,
    ]

    GetRandomSpawnMonsterID: Symbol[
        Optional[list[int]],
        None,
    ]

    NearbyAllyIqSkillIsEnabled: Symbol[
        Optional[list[int]],
        None,
    ]

    ResetGravity: Symbol[
        Optional[list[int]],
        None,
    ]

    GravityIsActive: Symbol[
        Optional[list[int]],
        None,
    ]

    TryActivateGravity: Symbol[
        Optional[list[int]],
        None,
    ]

    ShouldBoostKecleonShopSpawnChance: Symbol[
        Optional[list[int]],
        None,
    ]

    SetShouldBoostKecleonShopSpawnChance: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateShouldBoostKecleonShopSpawnChance: Symbol[
        Optional[list[int]],
        None,
    ]

    GetDoughSeedFlag: Symbol[
        Optional[list[int]],
        None,
    ]

    SetDoughSeedFlag: Symbol[
        Optional[list[int]],
        None,
    ]

    TrySpawnDoughSeedPoke: Symbol[
        Optional[list[int]],
        None,
    ]

    IsSecretBazaar: Symbol[
        Optional[list[int]],
        None,
    ]

    ShouldBoostHiddenStairsSpawnChance: Symbol[
        Optional[list[int]],
        None,
    ]

    SetShouldBoostHiddenStairsSpawnChance: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateShouldBoostHiddenStairsSpawnChance: Symbol[
        Optional[list[int]],
        None,
    ]

    IsSecretRoom: Symbol[
        Optional[list[int]],
        None,
    ]

    IsSecretFloor: Symbol[
        Optional[list[int]],
        None,
    ]

    GetCurrentHiddenStairsType: Symbol[
        Optional[list[int]],
        None,
    ]

    HiddenStairsPresent: Symbol[
        Optional[list[int]],
        None,
    ]

    PositionIsOnHiddenStairs: Symbol[
        Optional[list[int]],
        None,
    ]

    HiddenStairsTrigger: Symbol[
        Optional[list[int]],
        None,
    ]

    GetHiddenStairsField: Symbol[
        Optional[list[int]],
        None,
    ]

    SetHiddenStairsField: Symbol[
        Optional[list[int]],
        None,
    ]

    GetHiddenFloorField: Symbol[
        Optional[list[int]],
        None,
    ]

    SetHiddenFloorField: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMinimapData: Symbol[
        Optional[list[int]],
        None,
    ]

    DrawMinimapTile: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateMinimap: Symbol[
        Optional[list[int]],
        None,
    ]

    SetMinimapDataE447: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMinimapDataE447: Symbol[
        Optional[list[int]],
        None,
    ]

    SetMinimapDataE448: Symbol[
        Optional[list[int]],
        None,
    ]

    InitWeirdMinimapMatrix: Symbol[
        Optional[list[int]],
        None,
    ]

    InitMinimapDisplayTile: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadFixedRoomDataVeneer: Symbol[
        Optional[list[int]],
        None,
    ]

    UnloadFixedRoomData: Symbol[
        Optional[list[int]],
        None,
    ]

    IsNormalFloor: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateFloor: Symbol[
        Optional[list[int]],
        None,
    ]

    GetTileTerrain: Symbol[
        Optional[list[int]],
        None,
    ]

    DungeonRand100: Symbol[
        Optional[list[int]],
        None,
    ]

    ClearHiddenStairs: Symbol[
        Optional[list[int]],
        None,
    ]

    FlagHallwayJunctions: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateStandardFloor: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateOuterRingFloor: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateCrossroadsFloor: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateLineFloor: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateCrossFloor: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateBeetleFloor: Symbol[
        Optional[list[int]],
        None,
    ]

    MergeRoomsVertically: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateOuterRoomsFloor: Symbol[
        Optional[list[int]],
        None,
    ]

    IsNotFullFloorFixedRoom: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateFixedRoom: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateOneRoomMonsterHouseFloor: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateTwoRoomsWithMonsterHouseFloor: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateExtraHallways: Symbol[
        Optional[list[int]],
        None,
    ]

    GetGridPositions: Symbol[
        Optional[list[int]],
        None,
    ]

    InitDungeonGrid: Symbol[
        Optional[list[int]],
        None,
    ]

    AssignRooms: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateRoomsAndAnchors: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateSecondaryStructures: Symbol[
        Optional[list[int]],
        None,
    ]

    AssignGridCellConnections: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateGridCellConnections: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateRoomImperfections: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateHallway: Symbol[
        Optional[list[int]],
        None,
    ]

    EnsureConnectedGrid: Symbol[
        Optional[list[int]],
        None,
    ]

    SetTerrainObstacleChecked: Symbol[
        Optional[list[int]],
        None,
    ]

    FinalizeJunctions: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateKecleonShop: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateMonsterHouse: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateMazeRoom: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateMaze: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateMazeLine: Symbol[
        Optional[list[int]],
        None,
    ]

    SetSpawnFlag5: Symbol[
        Optional[list[int]],
        None,
    ]

    IsNextToHallway: Symbol[
        Optional[list[int]],
        None,
    ]

    ResolveInvalidSpawns: Symbol[
        Optional[list[int]],
        None,
    ]

    ConvertSecondaryTerrainToChasms: Symbol[
        Optional[list[int]],
        None,
    ]

    EnsureImpassableTilesAreWalls: Symbol[
        Optional[list[int]],
        None,
    ]

    InitializeTile: Symbol[
        Optional[list[int]],
        None,
    ]

    ResetFloor: Symbol[
        Optional[list[int]],
        None,
    ]

    PosIsOutOfBounds: Symbol[
        Optional[list[int]],
        None,
    ]

    ShuffleSpawnPositions: Symbol[
        Optional[list[int]],
        None,
    ]

    MarkNonEnemySpawns: Symbol[
        Optional[list[int]],
        None,
    ]

    MarkEnemySpawns: Symbol[
        Optional[list[int]],
        None,
    ]

    SetSecondaryTerrainOnWall: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateSecondaryTerrainFormations: Symbol[
        Optional[list[int]],
        None,
    ]

    StairsAlwaysReachable: Symbol[
        Optional[list[int]],
        None,
    ]

    GetNextFixedRoomAction: Symbol[
        Optional[list[int]],
        None,
    ]

    ConvertWallsToChasms: Symbol[
        Optional[list[int]],
        None,
    ]

    ResetInnerBoundaryTileRows: Symbol[
        Optional[list[int]],
        None,
    ]

    ResetImportantSpawnPositions: Symbol[
        Optional[list[int]],
        None,
    ]

    SpawnStairs: Symbol[
        Optional[list[int]],
        None,
    ]

    GetHiddenStairsType: Symbol[
        Optional[list[int]],
        None,
    ]

    GetFinalKecleonShopSpawnChance: Symbol[
        Optional[list[int]],
        None,
    ]

    ResetHiddenStairsSpawn: Symbol[
        Optional[list[int]],
        None,
    ]

    PlaceFixedRoomTile: Symbol[
        Optional[list[int]],
        None,
    ]

    FixedRoomActionParamToDirection: Symbol[
        Optional[list[int]],
        None,
    ]

    ApplyKeyEffect: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadFixedRoomData: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadFixedRoom: Symbol[
        Optional[list[int]],
        None,
    ]

    OpenFixedBin: Symbol[
        Optional[list[int]],
        None,
    ]

    CloseFixedBin: Symbol[
        Optional[list[int]],
        None,
    ]

    AreOrbsAllowed: Symbol[
        Optional[list[int]],
        None,
    ]

    AreTileJumpsAllowed: Symbol[
        Optional[list[int]],
        None,
    ]

    AreTrawlOrbsAllowed: Symbol[
        Optional[list[int]],
        None,
    ]

    AreOrbsAllowedVeneer: Symbol[
        Optional[list[int]],
        None,
    ]

    AreLateGameTrapsEnabled: Symbol[
        Optional[list[int]],
        None,
    ]

    AreMovesEnabled: Symbol[
        Optional[list[int]],
        None,
    ]

    IsRoomIlluminated: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMatchingMonsterId: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateItemExplicit: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateAndSpawnItem: Symbol[
        Optional[list[int]],
        None,
    ]

    IsHiddenStairsFloor: Symbol[
        Optional[list[int]],
        None,
    ]

    IsSecretBazaarVeneer: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateStandardItem: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateCleanItem: Symbol[
        Optional[list[int]],
        None,
    ]

    TryLeaderItemPickUp: Symbol[
        Optional[list[int]],
        None,
    ]

    SpawnItem: Symbol[
        Optional[list[int]],
        None,
    ]

    RemoveGroundItem: Symbol[
        Optional[list[int]],
        None,
    ]

    SpawnDroppedItemWrapper: Symbol[
        Optional[list[int]],
        None,
    ]

    SpawnDroppedItem: Symbol[
        Optional[list[int]],
        None,
    ]

    TryGenerateUnownStoneDrop: Symbol[
        Optional[list[int]],
        None,
    ]

    HasHeldItem: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateMoneyQuantity: Symbol[
        Optional[list[int]],
        None,
    ]

    CheckTeamItemsFlags: Symbol[
        Optional[list[int]],
        None,
    ]

    AddHeldItemToBag: Symbol[
        Optional[list[int]],
        None,
    ]

    RemoveEmptyItemsInBagWrapper: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateItem: Symbol[
        Optional[list[int]],
        None,
    ]

    DoesProjectileHitTarget: Symbol[
        Optional[list[int]],
        None,
    ]

    DisplayFloorCard: Symbol[
        Optional[list[int]],
        None,
    ]

    HandleFloorCard: Symbol[
        Optional[list[int]],
        None,
    ]

    CheckActiveChallengeRequest: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMissionDestination: Symbol[
        Optional[list[int]],
        None,
    ]

    IsOutlawOrChallengeRequestFloor: Symbol[
        Optional[list[int]],
        None,
    ]

    IsDestinationFloor: Symbol[
        Optional[list[int]],
        None,
    ]

    IsCurrentMissionType: Symbol[
        Optional[list[int]],
        None,
    ]

    IsCurrentMissionTypeExact: Symbol[
        Optional[list[int]],
        None,
    ]

    IsOutlawMonsterHouseFloor: Symbol[
        Optional[list[int]],
        None,
    ]

    IsGoldenChamber: Symbol[
        Optional[list[int]],
        None,
    ]

    IsLegendaryChallengeFloor: Symbol[
        Optional[list[int]],
        None,
    ]

    IsJirachiChallengeFloor: Symbol[
        Optional[list[int]],
        None,
    ]

    IsDestinationFloorWithMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    LoadMissionMonsterSprites: Symbol[
        Optional[list[int]],
        None,
    ]

    MissionTargetEnemyIsDefeated: Symbol[
        Optional[list[int]],
        None,
    ]

    SetMissionTargetEnemyDefeated: Symbol[
        Optional[list[int]],
        None,
    ]

    IsDestinationFloorWithFixedRoom: Symbol[
        Optional[list[int]],
        None,
    ]

    GetItemToRetrieve: Symbol[
        Optional[list[int]],
        None,
    ]

    GetItemToDeliver: Symbol[
        Optional[list[int]],
        None,
    ]

    GetSpecialTargetItem: Symbol[
        Optional[list[int]],
        None,
    ]

    IsDestinationFloorWithItem: Symbol[
        Optional[list[int]],
        None,
    ]

    IsDestinationFloorWithHiddenOutlaw: Symbol[
        Optional[list[int]],
        None,
    ]

    IsDestinationFloorWithFleeingOutlaw: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMissionTargetEnemy: Symbol[
        Optional[list[int]],
        None,
    ]

    GetMissionEnemyMinionGroup: Symbol[
        Optional[list[int]],
        None,
    ]

    SetTargetMonsterNotFoundFlag: Symbol[
        Optional[list[int]],
        None,
    ]

    GetTargetMonsterNotFoundFlag: Symbol[
        Optional[list[int]],
        None,
    ]

    FloorHasMissionMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    GenerateMissionEggMonster: Symbol[
        Optional[list[int]],
        None,
    ]

    LogMessageByIdWithPopupCheckParticipants: Symbol[
        Optional[list[int]],
        None,
    ]

    LogMessageByIdWithPopupCheckUser: Symbol[
        Optional[list[int]],
        None,
    ]

    LogMessageWithPopupCheckUser: Symbol[
        Optional[list[int]],
        None,
    ]

    LogMessageByIdQuiet: Symbol[
        Optional[list[int]],
        None,
    ]

    LogMessageQuiet: Symbol[
        Optional[list[int]],
        None,
    ]

    LogMessageByIdWithPopupCheckUserTarget: Symbol[
        Optional[list[int]],
        None,
    ]

    LogMessageWithPopupCheckUserTarget: Symbol[
        Optional[list[int]],
        None,
    ]

    LogMessageByIdQuietCheckUserTarget: Symbol[
        Optional[list[int]],
        None,
    ]

    LogMessageByIdWithPopupCheckUserUnknown: Symbol[
        Optional[list[int]],
        None,
    ]

    LogMessageByIdWithPopup: Symbol[
        Optional[list[int]],
        None,
    ]

    LogMessageWithPopup: Symbol[
        Optional[list[int]],
        None,
    ]

    LogMessage: Symbol[
        Optional[list[int]],
        None,
    ]

    LogMessageById: Symbol[
        Optional[list[int]],
        None,
    ]

    InitPortraitDungeon: Symbol[
        Optional[list[int]],
        None,
    ]

    OpenMessageLog: Symbol[
        Optional[list[int]],
        None,
    ]

    RunDungeonMode: Symbol[
        Optional[list[int]],
        None,
    ]

    StartFadeDungeon: Symbol[
        Optional[list[int]],
        None,
    ]

    StartFadeDungeonWrapper: Symbol[
        Optional[list[int]],
        None,
    ]

    HandleFadesDungeon: Symbol[
        Optional[list[int]],
        None,
    ]

    HandleFadesDungeonBothScreens: Symbol[
        Optional[list[int]],
        None,
    ]

    DisplayFloorTip: Symbol[
        Optional[list[int]],
        None,
    ]

    DisplayItemTip: Symbol[
        Optional[list[int]],
        None,
    ]

    DisplayDungeonTip: Symbol[
        Optional[list[int]],
        None,
    ]

    SetBothScreensWindowColorToDefault: Symbol[
        Optional[list[int]],
        None,
    ]

    GetPersonalityIndex: Symbol[
        Optional[list[int]],
        None,
    ]

    DisplayMessage: Symbol[
        Optional[list[int]],
        None,
    ]

    DisplayMessage2: Symbol[
        Optional[list[int]],
        None,
    ]

    YesNoMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    DisplayMessageInternal: Symbol[
        Optional[list[int]],
        None,
    ]

    OpenMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    OthersMenuLoop: Symbol[
        Optional[list[int]],
        None,
    ]

    OthersMenu: Symbol[
        Optional[list[int]],
        None,
    ]


class Overlay29DataProtocol(Protocol):

    DUNGEON_STRUCT_SIZE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MAX_HP_CAP: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OFFSET_OF_DUNGEON_FLOOR_PROPERTIES: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SPAWN_RAND_MAX: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_PRNG_LCG_MULTIPLIER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_PRNG_LCG_INCREMENT_SECONDARY: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ATTACK_SPRITE_BUFFER_SIZE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    KECLEON_FEMALE_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    KECLEON_MALE_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MSG_ID_SLOW_START: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EXPERIENCE_POINT_GAIN_CAP: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    JUDGMENT_MOVE_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    REGULAR_ATTACK_MOVE_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DEOXYS_ATTACK_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DEOXYS_SPEED_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    GIRATINA_ALTERED_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    PUNISHMENT_MOVE_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OFFENSE_STAT_MAX: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    PROJECTILE_MOVE_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BELLY_LOST_PER_TURN: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MONSTER_HEAL_HP_MAX: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MOVE_TARGET_AND_RANGE_SPECIAL_USER_HEALING: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    PLAIN_SEED_STRING_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MAX_ELIXIR_PP_RESTORATION: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SLIP_SEED_FAIL_STRING_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ROCK_WRECKER_MOVE_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    CASTFORM_NORMAL_FORM_MALE_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    CASTFORM_NORMAL_FORM_FEMALE_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    CHERRIM_SUNSHINE_FORM_MALE_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    CHERRIM_OVERCAST_FORM_FEMALE_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    CHERRIM_SUNSHINE_FORM_FEMALE_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    FLOOR_GENERATION_STATUS_PTR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OFFSET_OF_DUNGEON_N_NORMAL_ITEM_SPAWNS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_GRID_COLUMN_BYTES: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DEFAULT_MAX_POSITION: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OFFSET_OF_DUNGEON_GUARANTEED_ITEM_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    FIXED_ROOM_TILE_SPAWN_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TREASURE_BOX_1_ITEM_IDS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    FIXED_ROOM_REVISIT_OVERRIDES: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    FIXED_ROOM_MONSTER_SPAWN_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    FIXED_ROOM_ITEM_SPAWN_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    FIXED_ROOM_ENTITY_SPAWN_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STATUS_ICON_ARRAY_MUZZLED: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STATUS_ICON_ARRAY_MAGNET_RISE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STATUS_ICON_ARRAY_MIRACLE_EYE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STATUS_ICON_ARRAY_LEECH_SEED: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STATUS_ICON_ARRAY_LONG_TOSS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STATUS_ICON_ARRAY_BLINDED: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STATUS_ICON_ARRAY_BURN: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STATUS_ICON_ARRAY_SURE_SHOT: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STATUS_ICON_ARRAY_INVISIBLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STATUS_ICON_ARRAY_SLEEP: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STATUS_ICON_ARRAY_CURSE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STATUS_ICON_ARRAY_FREEZE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STATUS_ICON_ARRAY_CRINGE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STATUS_ICON_ARRAY_BIDE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STATUS_ICON_ARRAY_REFLECT: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DIRECTIONS_XY: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DISPLACEMENTS_WITHIN_2_LARGEST_FIRST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DISPLACEMENTS_WITHIN_2_SMALLEST_FIRST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DISPLACEMENTS_WITHIN_3: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ITEM_CATEGORY_ACTIONS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    FRACTIONAL_TURN_SEQUENCE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BELLY_DRAIN_IN_WALLS_INT: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BELLY_DRAIN_IN_WALLS_THOUSANDTHS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DAMAGE_MULTIPLIER_0_5: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DAMAGE_MULTIPLIER_1_5: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DAMAGE_MULTIPLIER_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    CLOUDY_DAMAGE_MULTIPLIER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SOLID_ROCK_MULTIPLIER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DAMAGE_FORMULA_MAX_BASE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    WONDER_GUARD_MULTIPLIER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DAMAGE_FORMULA_MIN_BASE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TYPE_DAMAGE_NEGATING_EXCLUSIVE_ITEM_EFFECTS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TWO_TURN_MOVES_AND_STATUSES: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SPATK_STAT_IDX: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ATK_STAT_IDX: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ROLLOUT_DAMAGE_MULT_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MAP_COLOR_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    CORNER_CARDINAL_NEIGHBOR_IS_OPEN: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    GUMMI_LIKE_STRING_IDS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    GUMMI_IQ_STRING_IDS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DAMAGE_STRING_IDS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_PTR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_PTR_MASTER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TOP_SCREEN_STATUS_PTR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LEADER_PTR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_PRNG_STATE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_PRNG_STATE_SECONDARY_VALUES: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LOADED_ATTACK_SPRITE_FILE_INDEX: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LOADED_ATTACK_SPRITE_PACK_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EXCL_ITEM_EFFECTS_WEATHER_ATK_SPEED_BOOST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EXCL_ITEM_EFFECTS_WEATHER_MOVE_SPEED_BOOST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EXCL_ITEM_EFFECTS_WEATHER_NO_STATUS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    AI_THROWN_ITEM_ACTION_CHOICE_COUNT: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    EXCL_ITEM_EFFECTS_EVASION_BOOST: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DEFAULT_TILE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    HIDDEN_STAIRS_SPAWN_BLOCKED: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    FIXED_ROOM_DATA_PTR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_FADES_PTR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    NECTAR_IQ_BOOST: Symbol[
        Optional[list[int]],
        None,
    ]

    COMPRESSED_SPRITE_BUFFER_SIZE: Symbol[
        Optional[list[int]],
        None,
    ]


Overlay29Protocol = SectionProtocol[
    Overlay29FunctionsProtocol,
    Overlay29DataProtocol,
    Optional[int],
]


class Overlay3FunctionsProtocol(Protocol):

    pass


class Overlay3DataProtocol(Protocol):

    pass


Overlay3Protocol = SectionProtocol[
    Overlay3FunctionsProtocol,
    Overlay3DataProtocol,
    Optional[int],
]


class Overlay30FunctionsProtocol(Protocol):

    WriteQuicksaveData: Symbol[
        Optional[list[int]],
        None,
    ]


class Overlay30DataProtocol(Protocol):

    OVERLAY30_JP_STRING_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY30_JP_STRING_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]


Overlay30Protocol = SectionProtocol[
    Overlay30FunctionsProtocol,
    Overlay30DataProtocol,
    Optional[int],
]


class Overlay31FunctionsProtocol(Protocol):

    EntryOverlay31: Symbol[
        Optional[list[int]],
        None,
    ]

    DrawDungeonMenuStatusWindow: Symbol[
        Optional[list[int]],
        None,
    ]

    DungeonMenuSwitch: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateStairsMenuState: Symbol[
        Optional[list[int]],
        None,
    ]

    StairsSubheadingCallback: Symbol[
        Optional[list[int]],
        None,
    ]

    HandleStairsMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    MovesMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    HandleMovesMenuWrapper0: Symbol[
        Optional[list[int]],
        None,
    ]

    HandleMovesMenuWrapper1: Symbol[
        Optional[list[int]],
        None,
    ]

    HandleMovesMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    TeamMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    RestMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    RecruitmentSearchMenuLoop: Symbol[
        Optional[list[int]],
        None,
    ]

    HelpMenuLoop: Symbol[
        Optional[list[int]],
        None,
    ]


class Overlay31DataProtocol(Protocol):

    DUNGEON_WINDOW_PARAMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_3: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_4: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_MAIN_MENU_ITEMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_MENU_SWITCH_STR1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY31_UNKNOWN_STRING_IDS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY31_UNKNOWN_STRUCT__NA_2389E30: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_5: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_6: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_7: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_SUBMENU_ITEMS_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_SUBMENU_ITEMS_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_SUBMENU_ITEMS_3: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_SUBMENU_ITEMS_4: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY31_UNKNOWN_STRUCT__NA_2389EF0: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_8: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_9: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_10: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_11: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_12: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_13: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY31_JP_STRING: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_14: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_15: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_16: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_17: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_18: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_19: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY31_UNKNOWN_STRUCT__NA_2389FE8: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_20: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_21: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_22: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_23: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_24: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_25: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_SUBMENU_ITEMS_5: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_26: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY31_UNKNOWN_STRUCT__NA_238A144: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_27: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_28: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY31_UNKNOWN_STRUCT__NA_238A190: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_SUBMENU_ITEMS_6: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_29: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_30: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_31: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_WINDOW_PARAMS_32: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY31_RESERVED_SPACE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY31_UNKNOWN_POINTER__NA_238A260: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY31_UNKNOWN_VALUE__NA_238A264: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY31_UNKNOWN_POINTER__NA_238A268: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY31_UNKNOWN_POINTER__NA_238A26C: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY31_UNKNOWN_POINTER__NA_238A270: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY31_UNKNOWN_POINTER__NA_238A274: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY31_UNKNOWN_POINTER__NA_238A278: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY31_UNKNOWN_POINTER__NA_238A27C: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY31_UNKNOWN_POINTER__NA_238A280: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY31_UNKNOWN_POINTER__NA_238A284: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY31_UNKNOWN_POINTER__NA_238A288: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY31_UNKNOWN_POINTER__NA_238A28C: Symbol[
        Optional[list[int]],
        Optional[int],
    ]


Overlay31Protocol = SectionProtocol[
    Overlay31FunctionsProtocol,
    Overlay31DataProtocol,
    Optional[int],
]


class Overlay32FunctionsProtocol(Protocol):

    pass


class Overlay32DataProtocol(Protocol):

    pass


Overlay32Protocol = SectionProtocol[
    Overlay32FunctionsProtocol,
    Overlay32DataProtocol,
    Optional[int],
]


class Overlay33FunctionsProtocol(Protocol):

    pass


class Overlay33DataProtocol(Protocol):

    pass


Overlay33Protocol = SectionProtocol[
    Overlay33FunctionsProtocol,
    Overlay33DataProtocol,
    Optional[int],
]


class Overlay34FunctionsProtocol(Protocol):

    ExplorersOfSkyMain: Symbol[
        Optional[list[int]],
        None,
    ]


class Overlay34DataProtocol(Protocol):

    OVERLAY34_UNKNOWN_STRUCT__NA_22DD014: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    START_MENU_ITEMS_CONFIRM: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY34_UNKNOWN_STRUCT__NA_22DD03C: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_DEBUG_MENU_ITEMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY34_RESERVED_SPACE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY34_UNKNOWN_POINTER__NA_22DD080: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY34_UNKNOWN_POINTER__NA_22DD084: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY34_UNKNOWN_POINTER__NA_22DD088: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY34_UNKNOWN_POINTER__NA_22DD08C: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    OVERLAY34_UNKNOWN_POINTER__NA_22DD090: Symbol[
        Optional[list[int]],
        Optional[int],
    ]


Overlay34Protocol = SectionProtocol[
    Overlay34FunctionsProtocol,
    Overlay34DataProtocol,
    Optional[int],
]


class Overlay35FunctionsProtocol(Protocol):

    pass


class Overlay35DataProtocol(Protocol):

    pass


Overlay35Protocol = SectionProtocol[
    Overlay35FunctionsProtocol,
    Overlay35DataProtocol,
    Optional[int],
]


class Overlay4FunctionsProtocol(Protocol):

    pass


class Overlay4DataProtocol(Protocol):

    pass


Overlay4Protocol = SectionProtocol[
    Overlay4FunctionsProtocol,
    Overlay4DataProtocol,
    Optional[int],
]


class Overlay5FunctionsProtocol(Protocol):

    pass


class Overlay5DataProtocol(Protocol):

    pass


Overlay5Protocol = SectionProtocol[
    Overlay5FunctionsProtocol,
    Overlay5DataProtocol,
    Optional[int],
]


class Overlay6FunctionsProtocol(Protocol):

    pass


class Overlay6DataProtocol(Protocol):

    pass


Overlay6Protocol = SectionProtocol[
    Overlay6FunctionsProtocol,
    Overlay6DataProtocol,
    Optional[int],
]


class Overlay7FunctionsProtocol(Protocol):

    pass


class Overlay7DataProtocol(Protocol):

    pass


Overlay7Protocol = SectionProtocol[
    Overlay7FunctionsProtocol,
    Overlay7DataProtocol,
    Optional[int],
]


class Overlay8FunctionsProtocol(Protocol):

    pass


class Overlay8DataProtocol(Protocol):

    pass


Overlay8Protocol = SectionProtocol[
    Overlay8FunctionsProtocol,
    Overlay8DataProtocol,
    Optional[int],
]


class Overlay9FunctionsProtocol(Protocol):

    CreateJukeboxTrackMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    CloseJukeboxTrackMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    IsJukeboxTrackMenuActive: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateJukeboxTrackMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    CreatePlaybackControlsMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    ClosePlaybackControlsMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    IsPlaybackControlsMenuActive: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdatePlaybackControlsMenu: Symbol[
        Optional[list[int]],
        None,
    ]

    CreateInputLockBox: Symbol[
        Optional[list[int]],
        None,
    ]

    CloseInputLockBox: Symbol[
        Optional[list[int]],
        None,
    ]

    IsInputLockBoxActive: Symbol[
        Optional[list[int]],
        None,
    ]

    UpdateInputLockBox: Symbol[
        Optional[list[int]],
        None,
    ]


class Overlay9DataProtocol(Protocol):

    JUKEBOX_TRACK_MENU_DEFAULT_WINDOW_PARAMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    PLAYBACK_CONTROLS_MENU_DEFAULT_WINDOW_PARAMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    INPUT_LOCK_BOX_DEFAULT_WINDOW_PARAMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TOP_MENU_RETURN_MUSIC_ID: Symbol[
        Optional[list[int]],
        None,
    ]


Overlay9Protocol = SectionProtocol[
    Overlay9FunctionsProtocol,
    Overlay9DataProtocol,
    Optional[int],
]


class RamFunctionsProtocol(Protocol):

    pass


class RamDataProtocol(Protocol):

    DEFAULT_MEMORY_ARENA_MEMORY: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    GROUND_MEMORY_ARENA_2: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    GROUND_MEMORY_ARENA_2_BLOCKS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    GROUND_MEMORY_ARENA_2_MEMORY: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_COLORMAP_PTR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DUNGEON_STRUCT: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MOVE_DATA_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SOUND_MEMORY_ARENA: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SOUND_MEMORY_ARENA_BLOCKS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SOUND_MEMORY_ARENA_MEMORY: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    FRAMES_SINCE_LAUNCH: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TOUCHSCREEN_STATUS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BAG_ITEMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BAG_ITEMS_PTR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STORAGE_ITEMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STORAGE_ITEM_QUANTITIES: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    KECLEON_SHOP_ITEMS_PTR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    KECLEON_SHOP_ITEMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    UNUSED_KECLEON_SHOP_ITEMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    KECLEON_WARES_ITEMS_PTR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    KECLEON_WARES_ITEMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    UNUSED_KECLEON_WARES_ITEMS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MONEY_CARRIED: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MONEY_STORED: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    AUDIO_COMMANDS_BUFFER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    CURSOR_16_SPRITE_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    CURSOR_SPRITE_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    CURSOR_ANIMATION_CONTROL: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    CURSOR_16_ANIMATION_CONTROL: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ALERT_SPRITE_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ALERT_ANIMATION_CONTROL: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SOUND_MEMORY_ARENA_PTR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    WINDOW_LIST: Symbol[
        Optional[list[int]],
        None,
    ]

    LAST_NEW_MOVE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SCRIPT_VARS_VALUES: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    BAG_LEVEL: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DEBUG_SPECIAL_EPISODE_NUMBER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    KAOMADO_STREAM: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    PENDING_DUNGEON_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    PENDING_STARTING_FLOOR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    PLAY_TIME_SECONDS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    PLAY_TIME_FRAME_COUNTER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TEAM_NAME: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LEVEL_UP_DATA_MONSTER_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LEVEL_UP_DATA_DECOMPRESS_BUFFER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TEAM_MEMBER_TABLE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    DRIVER_WORK: Symbol[
        Optional[list[int]],
        None,
    ]

    DISP_MODE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    GXI_VRAM_LOCK_ID: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ENABLED_VRAM_BANKS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SUB_BG_EXT_PLTT: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    CLR_IMG: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    THREAD_INFO_STRUCT: Symbol[
        Optional[list[int]],
        None,
    ]

    FRAMES_SINCE_LAUNCH_TIMES_THREE: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    GROUND_MEMORY_ARENA_1_PTR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    GROUND_MEMORY_ARENA_2_PTR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LOCK_NOTIFY_ARRAY: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    GROUND_MEMORY_ARENA_1: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    GROUND_MEMORY_ARENA_1_BLOCKS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    GROUND_MEMORY_ARENA_1_MEMORY: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    SENTRY_DUTY_STRUCT: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TURNING_ON_THE_SPOT_FLAG: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    LOADED_ATTACK_SPRITE_DATA: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    AI_THROWN_ITEM_DIRECTION_IS_USED: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    AI_THROWN_ITEM_DIRECTIONS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    AI_THROWN_ITEM_PROBABILITIES: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ROLLOUT_ICE_BALL_MISSED: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MULTIHIT_FATIGUE_MOVE_USED: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TWINEEDLE_HIT_TRACKER: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    RAPID_SPIN_BINDING_REMOVAL: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    ROLLOUT_ICE_BALL_SUCCESSIVE_HITS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    MULTIHIT_MOVE_SUCCESSIVE_HITS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    TRIPLE_KICK_SUCCESSIVE_HITS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    METRONOME_NEXT_INDEX: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    FLOOR_GENERATION_STATUS: Symbol[
        Optional[list[int]],
        Optional[int],
    ]

    STAIRS_MENU_PTR: Symbol[
        Optional[list[int]],
        Optional[int],
    ]


RamProtocol = SectionProtocol[
    RamFunctionsProtocol,
    RamDataProtocol,
    Optional[int],
]


class AllSymbolsProtocol(Protocol):

    arm7: Arm7Protocol

    arm9: Arm9Protocol

    itcm: ItcmProtocol

    libs: LibsProtocol

    move_effects: Move_effectsProtocol

    overlay0: Overlay0Protocol

    overlay1: Overlay1Protocol

    overlay10: Overlay10Protocol

    overlay11: Overlay11Protocol

    overlay12: Overlay12Protocol

    overlay13: Overlay13Protocol

    overlay14: Overlay14Protocol

    overlay15: Overlay15Protocol

    overlay16: Overlay16Protocol

    overlay17: Overlay17Protocol

    overlay18: Overlay18Protocol

    overlay19: Overlay19Protocol

    overlay2: Overlay2Protocol

    overlay20: Overlay20Protocol

    overlay21: Overlay21Protocol

    overlay22: Overlay22Protocol

    overlay23: Overlay23Protocol

    overlay24: Overlay24Protocol

    overlay25: Overlay25Protocol

    overlay26: Overlay26Protocol

    overlay27: Overlay27Protocol

    overlay28: Overlay28Protocol

    overlay29: Overlay29Protocol

    overlay3: Overlay3Protocol

    overlay30: Overlay30Protocol

    overlay31: Overlay31Protocol

    overlay32: Overlay32Protocol

    overlay33: Overlay33Protocol

    overlay34: Overlay34Protocol

    overlay35: Overlay35Protocol

    overlay4: Overlay4Protocol

    overlay5: Overlay5Protocol

    overlay6: Overlay6Protocol

    overlay7: Overlay7Protocol

    overlay8: Overlay8Protocol

    overlay9: Overlay9Protocol

    ram: RamProtocol
