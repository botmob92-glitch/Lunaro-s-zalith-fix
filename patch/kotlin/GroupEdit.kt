/*
 * Lunaro Client - group editing helpers for the controls editor.
 * Based on Zalith Launcher 2 (GPL-3.0). This file is part of the Lunaro Client patch.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 */

package com.movtery.layer_controller

import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.unit.IntSize
import com.movtery.layer_controller.data.ButtonSize
import com.movtery.layer_controller.data.JOYSTICK_MIN_SIZE_DP
import com.movtery.layer_controller.data.JOYSTICK_MIN_SIZE_PERCENTAGE
import com.movtery.layer_controller.data.MAX_SIZE_PERCENTAGE
import com.movtery.layer_controller.data.MIN_SIZE_DP
import com.movtery.layer_controller.data.MIN_SIZE_PERCENTAGE
import com.movtery.layer_controller.observable.ObservableJoystickData
import com.movtery.layer_controller.observable.ObservableWidget
import com.movtery.layer_controller.utils.getWidgetPosition
import com.movtery.layer_controller.utils.toPercentagePosition
import kotlin.math.roundToInt

/** How a group of selected widgets is aligned to each other. */
enum class GroupAlign { LEFT, RIGHT, TOP, BOTTOM, CENTER_X, CENTER_Y }

/**
 * Edits several widgets at once. All positions are handled in screen pixels and converted back
 * with the same percentage math the single-widget editor uses.
 */
object GroupEdit {

    private fun ready(widgets: List<ObservableWidget>): List<ObservableWidget> =
        widgets.filter { it.internalRenderSize != IntSize.Zero }

    private fun topLeftOf(widget: ObservableWidget, screen: IntSize): Offset =
        getWidgetPosition(widget, widget.internalRenderSize, screen)

    private fun placeTopLeft(widget: ObservableWidget, topLeft: Offset, screen: IntSize) {
        widget.putRenderPosition(topLeft.toPercentagePosition(widget.internalRenderSize, screen))
    }

    /** Moves every widget by the same pixel amount. The whole group stops at the screen edge. */
    fun moveBy(widgets: List<ObservableWidget>, dx: Float, dy: Float, screen: IntSize) {
        val list = ready(widgets)
        if (list.isEmpty()) return
        val lowX = list.maxOf { -topLeftOf(it, screen).x }
        val highX = list.minOf { (screen.width - it.internalRenderSize.width) - topLeftOf(it, screen).x }
        val lowY = list.maxOf { -topLeftOf(it, screen).y }
        val highY = list.minOf { (screen.height - it.internalRenderSize.height) - topLeftOf(it, screen).y }
        val cdx = dx.coerceIn(lowX, maxOf(lowX, highX))
        val cdy = dy.coerceIn(lowY, maxOf(lowY, highY))
        list.forEach { w ->
            val tl = topLeftOf(w, screen)
            placeTopLeft(w, Offset(tl.x + cdx, tl.y + cdy), screen)
        }
    }

    private fun referencePx(reference: ButtonSize.Reference, screen: IntSize): Int = when (reference) {
        ButtonSize.Reference.ScreenWidth -> screen.width
        ButtonSize.Reference.ScreenHeight -> screen.height
    }

    /** Makes every widget bigger (factor > 1) or smaller (factor < 1), keeping its top-left corner. */
    fun scaleBy(widgets: List<ObservableWidget>, factor: Float, screen: IntSize, density: Float) {
        ready(widgets).forEach { w ->
            val old = w.widgetSize
            if (old.type == ButtonSize.Type.WrapContent) return@forEach
            val isJoystick = w is ObservableJoystickData
            val minDp = if (isJoystick) JOYSTICK_MIN_SIZE_DP else MIN_SIZE_DP
            val minPct = if (isJoystick) JOYSTICK_MIN_SIZE_PERCENTAGE else MIN_SIZE_PERCENTAGE
            val tl = topLeftOf(w, screen)

            val newSize: ButtonSize = when (old.type) {
                ButtonSize.Type.Dp -> {
                    val maxW = if (isJoystick) minOf(screen.width, screen.height) / density else screen.width / density
                    val maxH = if (isJoystick) minOf(screen.width, screen.height) / density else screen.height / density
                    old.copy(
                        widthDp = (old.widthDp * factor).coerceIn(minDp, maxOf(minDp, maxW)),
                        heightDp = (old.heightDp * factor).coerceIn(minDp, maxOf(minDp, maxH))
                    )
                }
                ButtonSize.Type.Percentage -> old.copy(
                    widthPercentage = (old.widthPercentage * factor).roundToInt().coerceIn(minPct, MAX_SIZE_PERCENTAGE),
                    heightPercentage = (old.heightPercentage * factor).roundToInt().coerceIn(minPct, MAX_SIZE_PERCENTAGE)
                )
                else -> old
            }

            val newPx: IntSize = when (newSize.type) {
                ButtonSize.Type.Dp -> IntSize(
                    (newSize.widthDp * density).roundToInt(),
                    (newSize.heightDp * density).roundToInt()
                )
                ButtonSize.Type.Percentage -> IntSize(
                    (referencePx(newSize.widthReference, screen) * newSize.widthPercentage.toFloat() / MAX_SIZE_PERCENTAGE).roundToInt(),
                    (referencePx(newSize.heightReference, screen) * newSize.heightPercentage.toFloat() / MAX_SIZE_PERCENTAGE).roundToInt()
                )
                else -> w.internalRenderSize
            }

            w.putWidgetSize(newSize)
            w.putRenderPosition(tl.toPercentagePosition(newPx, screen))
        }
    }

    /** Aligns all widgets to the edge or the middle of the group's bounding box. */
    fun align(widgets: List<ObservableWidget>, mode: GroupAlign, screen: IntSize) {
        val list = ready(widgets)
        if (list.size < 2) return
        val tls = list.map { topLeftOf(it, screen) }
        val left = tls.minOf { it.x }
        val top = tls.minOf { it.y }
        val right = list.indices.maxOf { tls[it].x + list[it].internalRenderSize.width }
        val bottom = list.indices.maxOf { tls[it].y + list[it].internalRenderSize.height }
        list.forEachIndexed { i, w ->
            val s = w.internalRenderSize
            val tl = tls[i]
            val target = when (mode) {
                GroupAlign.LEFT -> Offset(left, tl.y)
                GroupAlign.RIGHT -> Offset(right - s.width, tl.y)
                GroupAlign.TOP -> Offset(tl.x, top)
                GroupAlign.BOTTOM -> Offset(tl.x, bottom - s.height)
                GroupAlign.CENTER_X -> Offset((left + right) / 2f - s.width / 2f, tl.y)
                GroupAlign.CENTER_Y -> Offset(tl.x, (top + bottom) / 2f - s.height / 2f)
            }
            placeTopLeft(w, target, screen)
        }
    }

    /** Spaces three or more widgets evenly between the first and the last one. */
    fun distribute(widgets: List<ObservableWidget>, horizontal: Boolean, screen: IntSize) {
        val list = ready(widgets)
        if (list.size < 3) return
        if (horizontal) {
            val sorted = list.sortedBy { topLeftOf(it, screen).x }
            val first = topLeftOf(sorted.first(), screen).x
            val last = topLeftOf(sorted.last(), screen).x + sorted.last().internalRenderSize.width
            val total = sorted.map { it.internalRenderSize.width }.sum()
            val gap = (last - first - total) / (sorted.size - 1)
            var x = first
            sorted.forEach { w ->
                val tl = topLeftOf(w, screen)
                placeTopLeft(w, Offset(x, tl.y), screen)
                x += w.internalRenderSize.width + gap
            }
        } else {
            val sorted = list.sortedBy { topLeftOf(it, screen).y }
            val first = topLeftOf(sorted.first(), screen).y
            val last = topLeftOf(sorted.last(), screen).y + sorted.last().internalRenderSize.height
            val total = sorted.map { it.internalRenderSize.height }.sum()
            val gap = (last - first - total) / (sorted.size - 1)
            var y = first
            sorted.forEach { w ->
                val tl = topLeftOf(w, screen)
                placeTopLeft(w, Offset(tl.x, y), screen)
                y += w.internalRenderSize.height + gap
            }
        }
    }
}
