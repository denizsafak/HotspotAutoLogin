#Requires AutoHotkey v2.0
#NoTrayIcon
try if ((pDesktopWallpaper := ComObject("{C2CF3110-460E-4fc1-B9D0-8A1C0C9CC4BD}", "{B92B56A9-8B55-4E14-9A89-0199BBB6F93B}"))) {
        ComCall(16, pDesktopWallpaper, "Ptr", 0, "UInt", 0) 
        ObjRelease(pDesktopWallpaper)
}