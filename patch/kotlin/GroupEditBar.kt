/*
 * Lunaro Client - bottom toolbar for editing several controls at once.
 * Based on Zalith Launcher 2 (GPL-3.0). This file is part of the Lunaro Client patch.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 */

package com.movtery.zalithlauncher.ui.screens.main.control_editor

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import com.movtery.layer_controller.GroupAlign
import com.movtery.layer_controller.GroupEdit
import com.movtery.layer_controller.observable.ObservableWidget

/**
 * Toolbar shown while "select more" mode is on: move, resize, align, space out or delete all
 * selected controls together.
 */
@Composable
fun GroupEditBar(
    widgets: List<ObservableWidget>,
    screenSize: IntSize,
    density: Float,
    onDelete: () -> Unit,
    onDone: () -> Unit,
    modifier: Modifier = Modifier
) {
    val steps = remember { intArrayOf(2, 5, 10, 20) }
    var stepIndex by remember { mutableIntStateOf(1) }
    val stepPx = steps[stepIndex] * density

    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(18.dp),
        color = MaterialTheme.colorScheme.surfaceContainerHigh,
        shadowElevation = 8.dp
    ) {
        Row(
            modifier = Modifier
                .horizontalScroll(rememberScrollState())
                .padding(horizontal = 12.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            Text(
                text = "${widgets.size} selected",
                style = MaterialTheme.typography.titleSmall
            )
            GroupChip("Step ${steps[stepIndex]}dp") { stepIndex = (stepIndex + 1) % steps.size }
            GroupChip("←") { GroupEdit.moveBy(widgets, -stepPx, 0f, screenSize) }
            GroupChip("↑") { GroupEdit.moveBy(widgets, 0f, -stepPx, screenSize) }
            GroupChip("↓") { GroupEdit.moveBy(widgets, 0f, stepPx, screenSize) }
            GroupChip("→") { GroupEdit.moveBy(widgets, stepPx, 0f, screenSize) }
            GroupChip("Smaller") { GroupEdit.scaleBy(widgets, 0.9f, screenSize, density) }
            GroupChip("Bigger") { GroupEdit.scaleBy(widgets, 1.1f, screenSize, density) }
            GroupChip("Align left") { GroupEdit.align(widgets, GroupAlign.LEFT, screenSize) }
            GroupChip("Align right") { GroupEdit.align(widgets, GroupAlign.RIGHT, screenSize) }
            GroupChip("Align top") { GroupEdit.align(widgets, GroupAlign.TOP, screenSize) }
            GroupChip("Align bottom") { GroupEdit.align(widgets, GroupAlign.BOTTOM, screenSize) }
            GroupChip("Center H") { GroupEdit.align(widgets, GroupAlign.CENTER_X, screenSize) }
            GroupChip("Center V") { GroupEdit.align(widgets, GroupAlign.CENTER_Y, screenSize) }
            GroupChip("Space H") { GroupEdit.distribute(widgets, true, screenSize) }
            GroupChip("Space V") { GroupEdit.distribute(widgets, false, screenSize) }
            FilledTonalButton(
                onClick = onDelete,
                enabled = widgets.isNotEmpty(),
                contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp),
                colors = ButtonDefaults.filledTonalButtonColors(
                    containerColor = MaterialTheme.colorScheme.errorContainer,
                    contentColor = MaterialTheme.colorScheme.onErrorContainer
                )
            ) {
                Text("Delete", style = MaterialTheme.typography.labelLarge)
            }
            Button(
                onClick = onDone,
                contentPadding = PaddingValues(horizontal = 16.dp, vertical = 4.dp)
            ) {
                Text("Done", style = MaterialTheme.typography.labelLarge)
            }
        }
    }
}

@Composable
private fun GroupChip(label: String, onClick: () -> Unit) {
    FilledTonalButton(
        onClick = onClick,
        contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp)
    ) {
        Text(label, style = MaterialTheme.typography.labelLarge)
    }
}

/** Pill shown on top of the editor while multi-select is on (or to explain how to turn it on). */
@Composable
fun MultiSelectBanner(text: String, modifier: Modifier = Modifier) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(50),
        color = MaterialTheme.colorScheme.primaryContainer,
        contentColor = MaterialTheme.colorScheme.onPrimaryContainer,
        shadowElevation = 6.dp
    ) {
        Text(
            text = text,
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
            style = MaterialTheme.typography.labelLarge
        )
    }
}
