/*
 * Lunaro Client - Smart Setup: looks at this phone and suggests mods, a shader and settings.
 * It is a rule-based recommender that runs on the phone itself (no internet, no online AI).
 * Part of the Lunaro Client patch for Zalith Launcher 2 (GPL-3.0).
 */

package com.movtery.zalithlauncher.ui.screens.main

import android.app.ActivityManager
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.os.Build
import android.widget.Toast
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp

enum class DeviceTier(val label: String) {
    LOW("Low-end"),
    MID("Mid-range"),
    HIGH("High-end")
}

data class DeviceInfo(
    val name: String,
    val chip: String,
    val ramGb: Float,
    val cores: Int
)

data class SetupPlan(
    val renderer: String,
    val renderDistance: Int,
    val shader: String,
    val mods: List<String>,
    val tips: List<String>
)

object DeviceProfiler {

    fun detect(context: Context): DeviceInfo {
        val am = context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        val mem = ActivityManager.MemoryInfo()
        am.getMemoryInfo(mem)
        val ramGb = mem.totalMem / (1024f * 1024f * 1024f)
        val socModel = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) Build.SOC_MODEL else ""
        val chip = listOf(socModel, Build.HARDWARE)
            .filter { it.isNotBlank() && !it.equals("unknown", ignoreCase = true) }
            .joinToString(" ")
        return DeviceInfo(
            name = "${Build.MANUFACTURER} ${Build.MODEL}",
            chip = chip,
            ramGb = ramGb,
            cores = Runtime.getRuntime().availableProcessors()
        )
    }

    private val weakChips = listOf(
        "mt65", "mt67", "sc98", "sc77", "ums", "sdm4", "sm4", "sdm6", "sm6",
        "exynos7", "exynos 7", "exynos850", "exynos 850", "s5e7"
    )
    private val midChips = listOf(
        "exynos8", "exynos 8", "exynos9", "exynos 9", "s5e8", "s5e9",
        "kirin6", "kirin 6", "kirin7", "kirin 7", "mt68", "helio", "sdm7", "sm7"
    )

    /** A rough guess from RAM, CPU cores and well-known older chip families. */
    fun autoTier(info: DeviceInfo): DeviceTier {
        val chip = info.chip.lowercase()
        var tier = when {
            info.ramGb < 4.5f || info.cores <= 4 -> DeviceTier.LOW
            info.ramGb >= 8f -> DeviceTier.HIGH
            else -> DeviceTier.MID
        }
        if (weakChips.any { chip.contains(it) }) {
            tier = DeviceTier.LOW
        } else if (tier == DeviceTier.HIGH && midChips.any { chip.contains(it) }) {
            tier = DeviceTier.MID
        }
        return tier
    }

    private val baseMods = listOf(
        "Sodium", "Lithium", "FerriteCore", "Entity Culling",
        "ImmediatelyFast", "BadOptimizations", "ScalableLux"
    )

    fun plan(tier: DeviceTier): SetupPlan = when (tier) {
        DeviceTier.LOW -> SetupPlan(
            renderer = "MobileGlues first, LTW if it crashes",
            renderDistance = 4,
            shader = "None. Shaders will not run smoothly on this class of phone.",
            mods = baseMods,
            tips = listOf(
                "Set the resolution scale to 60-75% in the game settings",
                "Keep simulation distance at 4",
                "Close other apps before launching"
            )
        )
        DeviceTier.MID -> SetupPlan(
            renderer = "MobileGlues first, LTW if it crashes",
            renderDistance = 6,
            shader = "MakeUp UltraFast on its lowest settings (expect a big FPS drop compared to no shaders)",
            mods = baseMods + listOf("Iris", "Sodium Extra", "Reese's Sodium Options", "Dynamic FPS"),
            tips = listOf(
                "Turn shadows off inside the shader options",
                "Resolution scale 75-85% while shaders are on",
                "Switch shaders off for a big FPS boost when you do not need them"
            )
        )
        DeviceTier.HIGH -> SetupPlan(
            renderer = "MobileGlues first, Zink or LTW if it looks wrong",
            renderDistance = 10,
            shader = "Complementary Reimagined on its lowest profile, or MakeUp UltraFast for more FPS",
            mods = baseMods + listOf("Iris", "Sodium Extra", "Reese's Sodium Options", "Dynamic FPS"),
            tips = listOf(
                "Start with shadows off, then raise one setting at a time",
                "Resolution scale 85-100%",
                "Watch for heat: long sessions can throttle the phone"
            )
        )
    }

    /** Advice about Minecraft versions and graphics settings that suits this phone. */
    fun versionTips(info: DeviceInfo): List<String> {
        val tips = mutableListOf(
            "Most stable on phones: Minecraft 1.21.11 or 26.1.",
            "Minecraft 26.2 and 26.3 are newer. In the version settings set Graphics API to OpenGL (not Vulkan) and use MobileGlues.",
            "If a version closes right after the mod list, try it without Sodium and shaders first to find the cause."
        )
        if (info.chip.lowercase().contains("exynos")) {
            tips.add("Most Exynos chips have a Mali GPU: MobileGlues or LTW work best, avoid Vulkan and Zink.")
        }
        return tips
    }

    fun asText(info: DeviceInfo, tier: DeviceTier, plan: SetupPlan): String = buildString {
        appendLine("Lunaro Client - Smart Setup")
        appendLine("Device: ${info.name} (${info.chip}, ${"%.1f".format(info.ramGb)} GB RAM, ${info.cores} cores)")
        appendLine("Class: ${tier.label}")
        appendLine("Renderer: ${plan.renderer}")
        appendLine("Render distance: ${plan.renderDistance}")
        appendLine("Shader: ${plan.shader}")
        appendLine("Mods: ${plan.mods.joinToString(", ")}")
        plan.tips.forEach { appendLine("- $it") }
        appendLine("Minecraft version:")
        versionTips(info).forEach { appendLine("- $it") }
    }
}

/** Dialog opened from the rocket button in the top bar. */
@Composable
fun SmartSetupDialog(onDismiss: () -> Unit) {
    val context = LocalContext.current
    val info = remember { DeviceProfiler.detect(context) }
    val auto = remember { DeviceProfiler.autoTier(info) }
    var picked by remember { mutableStateOf<DeviceTier?>(null) }
    val tier = picked ?: auto
    val plan = DeviceProfiler.plan(tier)

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Smart Setup") },
        text = {
            Column(
                modifier = Modifier.verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                Text(info.name, style = MaterialTheme.typography.titleMedium)
                Text(
                    "${info.chip} \u00B7 ${"%.1f".format(info.ramGb)} GB RAM \u00B7 ${info.cores} cores",
                    style = MaterialTheme.typography.bodySmall
                )
                Text(
                    "Detected as: ${auto.label}. This is an estimate, so change it below if it looks wrong.",
                    style = MaterialTheme.typography.bodySmall
                )
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    DeviceTier.values().forEach { t ->
                        if (t == tier) {
                            Button(onClick = { picked = t }) { Text(t.label) }
                        } else {
                            OutlinedButton(onClick = { picked = t }) { Text(t.label) }
                        }
                    }
                }
                Text("Renderer", style = MaterialTheme.typography.labelLarge)
                Text(plan.renderer)
                Text("Render distance", style = MaterialTheme.typography.labelLarge)
                Text("${plan.renderDistance} chunks")
                Text("Shader", style = MaterialTheme.typography.labelLarge)
                Text(plan.shader)
                Text("Mods", style = MaterialTheme.typography.labelLarge)
                Text(plan.mods.joinToString(", "))
                Text("Tips", style = MaterialTheme.typography.labelLarge)
                plan.tips.forEach { Text("\u2022 $it") }
                Text("Minecraft version", style = MaterialTheme.typography.labelLarge)
                DeviceProfiler.versionTips(info).forEach { Text("\u2022 $it") }
                Text(
                    "Rule-based suggestions that run on your phone. They are not an online AI.",
                    style = MaterialTheme.typography.bodySmall
                )
            }
        },
        confirmButton = {
            TextButton(onClick = {
                val cm = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                cm.setPrimaryClip(ClipData.newPlainText("Lunaro Smart Setup", DeviceProfiler.asText(info, tier, plan)))
                Toast.makeText(context, "Copied", Toast.LENGTH_SHORT).show()
            }) { Text("Copy list") }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Close") }
        }
    )
}
