from PyQt6.QtWidgets import QSplitter


def enable_free_resize(splitter: QSplitter) -> QSplitter:
    splitter.setChildrenCollapsible(True)
    splitter.setOpaqueResize(True)
    for index in range(splitter.count()):
        splitter.setCollapsible(index, True)
    return splitter
