#!/usr/bin/env python3
"""Rebrand a checkout of ZalithLauncher2 as "Lunaro Client".
Usage: python3 apply_lunaro.py <path-to-ZalithLauncher2-checkout>
Every edit asserts that the text it expects is really there, so a changed
upstream makes the build fail loudly instead of silently producing a half-patched app.
"""
import re, shutil, sys, pathlib

root = pathlib.Path(sys.argv[1]).resolve()
here = pathlib.Path(__file__).resolve().parent
app = root / "ZalithLauncher"
main = app / "src/main"
kt = main / "java/com/movtery/zalithlauncher"

def edit(path, fn):
    t = path.read_text(encoding="utf-8"); n = fn(t)
    assert n != t, f"no change made in {path}"
    path.write_text(n, encoding="utf-8")

def sub1(t, old, new):
    assert old in t, f"expected text not found: {old[:60]!r}"
    return t.replace(old, new, 1)

# 1. Name
edit(app / "gradle.properties", lambda t: sub1(sub1(t, "launcher_app_name=Zalith Launcher", "launcher_app_name=Lunaro Client"),
                                              "launcher_short_name=ZL2", "launcher_short_name=Lunaro"))
edit(app / "gradle.properties", lambda t: sub1(t, "launcher_name=ZalithLauncher", "launcher_name=LunaroClient"))
# 2. Own package id so it installs next to Zalith (code namespace stays untouched)
edit(app / "build.gradle.kts", lambda t: sub1(t, 'applicationIdSuffix = ".v2"', 'applicationIdSuffix = ".lunaro"'))
# 2b. Smooth build: a release-style variant ("lunaro": code shrinking on, no developer tooling) signed with
#     Zalith's own debug key. A plain debug build is much slower and feels laggy.
edit(app / "build.gradle.kts", lambda t: sub1(t,
    "        debug {\n            isMinifyEnabled = false\n",
    "        create(\"lunaro\") {\n"
    "            initWith(getByName(\"release\"))\n"
    "            signingConfig = signingConfigs.getByName(\"debugBuild\")\n"
    "            matchingFallbacks += listOf(\"release\")\n"
    "        }\n"
    "        debug {\n            isMinifyEnabled = false\n"))
edit(app / "build.gradle.kts", lambda t: sub1(t,
    'if (variant.buildType == "release")',
    'if (variant.buildType == "release" || variant.buildType == "lunaro")'))
# 3. Default: Lunaro theme, always (not wallpaper colours), dark mode on
edit(kt / "setting/AllSettings.kt", lambda t: sub1(t,
    "if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) ColorThemeType.DYNAMIC\n        else ColorThemeType.EMBERMIRE",
    "ColorThemeType.EMBERMIRE"))
edit(kt / "setting/AllSettings.kt", lambda t: sub1(t,
    'enumSetting("launcherDarkMode", DarkMode.FollowSystem)', 'enumSetting("launcherDarkMode", DarkMode.Enable)'))

# 3b. Snappier launcher UI by default: no page-transition animation, no festival effects
edit(kt / "setting/AllSettings.kt", lambda t: sub1(t,
    "enumSetting(\"launcherSwapAnimateType\", TransitionAnimationType.JELLY_BOUNCE)",
    "enumSetting(\"launcherSwapAnimateType\", TransitionAnimationType.CLOSE)"))
edit(kt / "setting/AllSettings.kt", lambda t: sub1(t,
    'boolSetting("launcherFestivalEffects", true)', 'boolSetting("launcherFestivalEffects", false)'))

# 3c. Minecraft 26.2+ has a Vulkan backend that fails on many phones. Force OpenGL for every instance by default
#     (upstream only suggests OpenGL when the game has no saved choice, so an old Vulkan value would stay).
edit(kt / "setting/AllSettings.kt", lambda t: sub1(t,
    'enumSetting("graphicsApi", GraphicsApi.DEFAULT_OPENGL)', 'enumSetting("graphicsApi", GraphicsApi.OPENGL)'))

# 4. Lunaro palette replaces the first ("embermire") column of every colour row
dark = dict(primary="C9B6FF", onPrimary="2E1A66", primaryContainer="5B3FD0", onPrimaryContainer="FFFFFF",
    secondary="C2C6F2", onSecondary="2A2F5B", secondaryContainer="3B4170", onSecondaryContainer="DDE0FF",
    tertiary="7FD7F2", onTertiary="00363F", tertiaryContainer="1B6B7D", onTertiaryContainer="C0F1FF",
    background="0D0B1A", onBackground="E6E1F5", surface="0D0B1A", onSurface="E6E1F5",
    surfaceVariant="2D2A45", onSurfaceVariant="C9C4DE", outline="938FA8", outlineVariant="474360",
    inverseSurface="E6E1F5", inverseOnSurface="312E42", inversePrimary="5B3FD0",
    surfaceDim="0D0B1A", surfaceBright="36334D", surfaceContainerLowest="08060F", surfaceContainerLow="15122A",
    surfaceContainer="191630", surfaceContainerHigh="241F3C", surfaceContainerHighest="2F2A48")
light = dict(primary="5B3FD0", onPrimary="FFFFFF", primaryContainer="E6DEFF", onPrimaryContainer="1A0A5C",
    secondary="5B5D8A", onSecondary="FFFFFF", secondaryContainer="E1E0FF", onSecondaryContainer="171A44",
    tertiary="006A7D", onTertiary="FFFFFF", tertiaryContainer="B6EBFF", onTertiaryContainer="001F27",
    background="FCF8FF", onBackground="1C1B22", surface="FCF8FF", onSurface="1C1B22",
    surfaceVariant="E5E0F0", onSurfaceVariant="47445A", outline="787590", outlineVariant="C9C4DE",
    inverseSurface="312E42", inverseOnSurface="F3EFFF", inversePrimary="C9B6FF",
    surfaceDim="DCD8E6", surfaceBright="FCF8FF", surfaceContainerLowest="FFFFFF", surfaceContainerLow="F6F2FF",
    surfaceContainer="F0ECFA", surfaceContainerHigh="EAE6F4", surfaceContainerHighest="E5E1EF")
def colors(t):
    done = 0
    for suffix, pal in (("Dark", dark), ("Light", light)):
        for name, hexv in pal.items():
            pat = re.compile(rf"(^val {name}{suffix} = ColorTheme\()Color\(0x[0-9A-Fa-f]{{8}}\)", re.M)
            t, k = pat.subn(rf"\1Color(0xFF{hexv})", t); assert k == 1, f"{name}{suffix}"; done += 1
    assert done == len(dark) + len(light)
    return t
edit(kt / "ui/theme/Color.kt", colors)
edit(kt / "ui/theme/NativeThemeUtils.kt", lambda t: sub1(t,
    "ColorThemeType.EMBERMIRE -> if (darkTheme) 0xFFFFB598.toInt() else 0xFFA63A17.toInt()",
    "ColorThemeType.EMBERMIRE -> if (darkTheme) 0xFFC9B6FF.toInt() else 0xFF5B3FD0.toInt()"))

# 6. Controls editor: select several controls and edit them together
def subu(t, old, new):
    assert t.count(old) == 1, f"expected exactly one match for: {old[:70]!r} (found {t.count(old)})"
    return t.replace(old, new, 1)

NEW_FILES = {
    "GroupEdit.kt": "LayerController/src/main/java/com/movtery/layer_controller/GroupEdit.kt",
    "GroupEditBar.kt": "ZalithLauncher/src/main/java/com/movtery/zalithlauncher/ui/screens/main/control_editor/GroupEditBar.kt",
    "SmartSetup.kt": "ZalithLauncher/src/main/java/com/movtery/zalithlauncher/ui/screens/main/SmartSetup.kt",
}
for name, dest in NEW_FILES.items():
    target = root / dest
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(here / "kotlin" / name, target)

edit(kt / "viewmodel/EditorViewModel.kt", lambda t: subu(t,
    "    var selectedWidget by mutableStateOf<SelectedWidgetData?>(null)\n",
    "    var selectedWidget by mutableStateOf<SelectedWidgetData?>(null)\n\n"
    "    /** Lunaro: is \"select more\" mode on in the controls editor */\n"
    "    var multiSelectMode by mutableStateOf(false)\n\n"
    "    /** Lunaro: controls picked while \"select more\" mode is on */\n"
    "    val multiSelection = androidx.compose.runtime.mutableStateListOf<SelectedWidgetData>()\n\n"
    "    /** Lunaro: short hint shown on top of the editor (e.g. how to start multi-select) */\n"
    "    var multiHint by mutableStateOf<String?>(null)\n"))

lc = root / "LayerController/src/main/java/com/movtery/layer_controller/ControlEditor.kt"
def layer_edit(t):
    t = subu(t, "    focusedLayer: ObservableControlLayer? = null,\n    isDark: Boolean = isSystemInDarkTheme(),",
                "    focusedLayer: ObservableControlLayer? = null,\n    multiSelected: List<ObservableWidget> = emptyList(),\n    isDark: Boolean = isSystemInDarkTheme(),")
    t = subu(t, "            //绘制调整大小的手柄\n",
"""            //Lunaro: outline every control picked in "select more" mode
            Canvas(modifier = Modifier.fillMaxSize()) {
                multiSelected.forEach { w ->
                    val s = w.internalRenderSize
                    if (s != IntSize.Zero) {
                        val p = getWidgetPosition(w, s, screenSize)
                        val pad = 4.dp.toPx()
                        drawRect(
                            color = primaryColor,
                            topLeft = Offset(p.x - pad, p.y - pad),
                            size = Size(s.width + pad * 2, s.height + pad * 2),
                            style = Stroke(width = 2.dp.toPx())
                        )
                    }
                }
            }

            //绘制调整大小的手柄
""")
    return t
edit(lc, layer_edit)

screen = main / "java/com/movtery/zalithlauncher/ui/screens/main/control_editor/ControlEditor.kt"
def screen_edit(t):
    t = subu(t, "import androidx.compose.foundation.layout.fillMaxSize\n",
                "import androidx.compose.foundation.layout.fillMaxSize\nimport androidx.compose.foundation.layout.fillMaxWidth\n")
    t = subu(t, "    val screenSize = rememberBoxSize()\n",
                "    val screenSize = rememberBoxSize()\n    var confirmGroupDelete by remember { mutableStateOf(false) }\n")
    t = subu(t, "            selectedWidget = viewModel.selectedWidget?.data,\n",
                "            selectedWidget = viewModel.selectedWidget?.data,\n            multiSelected = viewModel.multiSelection.map { it.data },\n")
    t = subu(t, """            onButtonTap = { data, layer ->
                val current = viewModel.selectedWidget?.data
                viewModel.selectedWidget = SelectedWidgetData(data, layer)
                if (current == data) {
                    //选中后再点击一次，打开编辑菜单
                    viewModel.editorOperation = EditorOperation.SelectButton
                }
            },
            onBackgroundClick = {
                //点击背景层时清除选中的控件
                viewModel.selectedWidget = null
            },
""", """            onButtonTap = { data, layer ->
                if (viewModel.multiSelectMode) {
                    //Lunaro: "select more" mode, tap to add or remove a control
                    val index = viewModel.multiSelection.indexOfFirst { it.data == data }
                    if (index >= 0) {
                        viewModel.multiSelection.removeAt(index)
                    } else {
                        viewModel.multiSelection.add(SelectedWidgetData(data, layer))
                    }
                } else {
                    val current = viewModel.selectedWidget?.data
                    viewModel.selectedWidget = SelectedWidgetData(data, layer)
                    if (current == data) {
                        //选中后再点击一次，打开编辑菜单
                        viewModel.editorOperation = EditorOperation.SelectButton
                    }
                }
            },
            onBackgroundClick = {
                //点击背景层时清除选中的控件（"select more" 模式下保留选择）
                if (!viewModel.multiSelectMode) {
                    viewModel.selectedWidget = null
                }
            },
""")
    t = subu(t, "            floatingButtons = {\n                //设置属性\n",
"""            floatingButtons = {
                //Lunaro: start selecting several controls
                var lastMultiTap by remember { mutableStateOf(0L) }
                ActionButton(
                    painter = painterResource(R.drawable.ic_add_box_filled),
                    text = "Multi-select",
                    onClick = {
                        val now = System.currentTimeMillis()
                        if (now - lastMultiTap <= 450L) {
                            //double tap: start multi-select mode
                            val widget = viewModel.selectedWidget
                            if (widget != null) {
                                viewModel.multiSelection.clear()
                                viewModel.multiSelection.add(widget)
                                viewModel.selectedWidget = null
                                viewModel.multiSelectMode = true
                                viewModel.multiHint = null
                            }
                            lastMultiTap = 0L
                        } else {
                            lastMultiTap = now
                            viewModel.multiHint = "Double-tap fast to turn on multi-select"
                        }
                    }
                )
                //Lunaro: one-tap switch between selecting one control and selecting several
                ActionButton(
                    painter = painterResource(R.drawable.ic_add_box_filled),
                    text = if (viewModel.multiSelectMode) "Select: Multi" else "Select: One",
                    onClick = {
                        if (viewModel.multiSelectMode) {
                            viewModel.multiSelection.clear()
                            viewModel.multiSelectMode = false
                        } else {
                            viewModel.multiSelection.clear()
                            viewModel.selectedWidget?.let { viewModel.multiSelection.add(it) }
                            viewModel.selectedWidget = null
                            viewModel.multiSelectMode = true
                        }
                        viewModel.multiHint = null
                    }
                )
                //设置属性
""")
    t = subu(t, "    EditorMenu(\n        state = viewModel.editorMenu,\n",
"""    androidx.compose.runtime.LaunchedEffect(viewModel.multiHint) {
        if (viewModel.multiHint != null) {
            kotlinx.coroutines.delay(2000L)
            viewModel.multiHint = null
        }
    }
    val multiBanner = if (viewModel.multiSelectMode) {
        "Multi-select mode ON \u2013 tap controls to add or remove them"
    } else {
        viewModel.multiHint
    }
    if (multiBanner != null && !viewModel.isPreviewMode) {
        MultiSelectBanner(
            text = multiBanner,
            modifier = Modifier
                .align(Alignment.TopCenter)
                .padding(top = 12.dp)
        )
    }

    if (viewModel.multiSelectMode && !viewModel.isPreviewMode) {
        GroupEditBar(
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .padding(bottom = 12.dp)
                .fillMaxWidth(0.94f),
            widgets = viewModel.multiSelection.map { it.data },
            screenSize = screenSize,
            density = density.density,
            onDelete = { confirmGroupDelete = true },
            onDone = {
                viewModel.multiSelection.clear()
                viewModel.multiSelectMode = false
            }
        )
    }

    if (confirmGroupDelete) {
        SimpleAlertDialog(
            title = stringResource(R.string.generic_delete),
            text = "Delete ${viewModel.multiSelection.size} selected controls?",
            onDismiss = { confirmGroupDelete = false },
            onConfirm = {
                viewModel.multiSelection.toList().forEach { viewModel.removeWidget(it.layer, it.data) }
                viewModel.multiSelection.clear()
                viewModel.multiSelectMode = false
                confirmGroupDelete = false
            }
        )
    }

    EditorMenu(
        state = viewModel.editorMenu,
""")
    return t
edit(screen, screen_edit)

# 7. Lunar-style look: rounder panels, wordmark title, big PLAY button (original design, no Lunar assets)
def add_import(t, line):
    if line in t: return t
    assert "\nimport " in t
    return t.replace("\nimport ", "\n" + line + "\nimport ", 1)

theme = kt / "ui/theme/Theme.kt"
def theme_edit(t):
    t = subu(t, "            typography = AppTypography,\n            content = content",
"""            typography = AppTypography,
            shapes = androidx.compose.material3.Shapes(
                extraSmall = RoundedCornerShape(6.dp),
                small = RoundedCornerShape(10.dp),
                medium = RoundedCornerShape(14.dp),
                large = RoundedCornerShape(18.dp),
                extraLarge = RoundedCornerShape(26.dp)
            ),
            content = content""")
    t = add_import(t, "import androidx.compose.foundation.shape.RoundedCornerShape")
    t = add_import(t, "import androidx.compose.ui.unit.dp")
    return t
edit(theme, theme_edit)

mainscreen = kt / "ui/screens/main/MainScreen.kt"
def main_edit(t):
    t = subu(t, "                            text = BuildKeys.LAUNCHER_IDENTIFIER,\n                            style = style,",
"""                            text = BuildKeys.LAUNCHER_NAME.uppercase(),
                            style = style.copy(
                                fontWeight = FontWeight.Bold,
                                letterSpacing = 3.sp,
                                color = MaterialTheme.colorScheme.primary
                            ),""")
    t = add_import(t, "import androidx.compose.ui.text.font.FontWeight")
    t = add_import(t, "import androidx.compose.ui.unit.sp")
    return t
edit(mainscreen, main_edit)

launcher = kt / "ui/screens/content/LauncherScreen.kt"
def launcher_edit(t):
    t = subu(t, """                .padding(PaddingValues(horizontal = 12.dp))
                .padding(bottom = 8.dp),
            elevation = ButtonDefaults.buttonElevation(defaultElevation = 1.dp),
            onClick = {
                onLaunchGame(null)
            },""", """                .padding(PaddingValues(horizontal = 12.dp))
                .padding(bottom = 8.dp)
                .height(58.dp),
            shape = RoundedCornerShape(18.dp),
            elevation = ButtonDefaults.buttonElevation(defaultElevation = 6.dp),
            onClick = {
                onLaunchGame(null)
            },""")
    t = add_import(t, "import androidx.compose.foundation.layout.height")
    t = add_import(t, "import androidx.compose.foundation.shape.RoundedCornerShape")
    return t
edit(launcher, launcher_edit)

# 8. Smart Setup button (device-based suggestions) and a bigger download read buffer
def smart_edit(t):
    t = subu(t, "    val inMultiplayerScreen = mainScreenKey is NormalNavKey.Multiplayer\n",
"""    val showSmartSetup = remember { androidx.compose.runtime.mutableStateOf(false) }
    if (showSmartSetup.value) {
        SmartSetupDialog(onDismiss = { showSmartSetup.value = false })
    }

    val inMultiplayerScreen = mainScreenKey is NormalNavKey.Multiplayer
""")
    t = subu(t, """                IconButton(
                    onClick = openFileManager
                ) {""", """                IconButton(
                    onClick = { showSmartSetup.value = true }
                ) {
                    Icon(
                        painter = painterResource(R.drawable.ic_rocket_launch_filled),
                        contentDescription = "Smart Setup"
                    )
                }

                IconButton(
                    onClick = openFileManager
                ) {""")
    return t
edit(mainscreen, smart_edit)

edit(kt / "game/download/engine/Fetcher.kt", lambda t: subu(t,
    "    private const val BUFFER_SIZE = 32 * 1024", "    private const val BUFFER_SIZE = 128 * 1024"))

# 5. Icons
res = main / "res"
for f in (here / "res").rglob("*"):
    if f.is_file():
        dst = res / f.relative_to(here / "res"); dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy(f, dst)
print("Lunaro Client patch applied to", root)
