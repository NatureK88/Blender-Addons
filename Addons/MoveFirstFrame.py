# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Copyright (C) 2026 Liuzhenming


# 对齐选中关键帧的第一个到当前帧，用于整体平移动作


bl_info = {
    "name": "LZM_Move First Frame",
    "author": "Liuzhenming",
    "version": (1, 2, 0),
    "blender": (5, 0, 0),
    "location": "Dopesheet (default: Shift + N)",
    "description": "Aligns the earliest selected keyframe of each selected object to the current frame.",
    "category": "Animation",
}

import bpy
import rna_keymap_ui

addon_keymaps = []


# --------------------------------------------------
# Operator
# --------------------------------------------------

class ANIM_OT_move_first_frame(bpy.types.Operator):
    bl_idname = "anim.move_first_frame"
    bl_label = "Move First Keyframe To Current Frame"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        current_frame = scene.frame_current

        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'ERROR'}, "没有选中的对象")
            return {'CANCELLED'}

        moved_any = False

        for obj in selected_objects:
            adt = obj.animation_data
            if not adt or not adt.action:
                continue

            action = adt.action

            selected_kps = []
            earliest_frame = None

            # Action → Layers → Strips → ChannelBags → FCurves
            for layer in action.layers:
                for strip in layer.strips:
                    for cb in strip.channelbags:
                        for fcu in cb.fcurves:
                            for kp in fcu.keyframe_points:
                                if kp.select_control_point:
                                    frame = kp.co.x
                                    selected_kps.append(kp)

                                    if earliest_frame is None or frame < earliest_frame:
                                        earliest_frame = frame

            if not selected_kps:
                continue

            delta = current_frame - earliest_frame

            for kp in selected_kps:
                kp.co.x += delta
                kp.handle_left.x += delta
                kp.handle_right.x += delta

            moved_any = True

        if not moved_any:
            self.report({'WARNING'}, "选中的对象中没有可移动的关键帧")
            return {'CANCELLED'}

        return {'FINISHED'}


# --------------------------------------------------
# Addon Preferences
# --------------------------------------------------

class MoveFirstFramePreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    def draw(self, context):
        layout = self.layout
        layout.label(text="Shortcut:")

        wm = context.window_manager
        kc = wm.keyconfigs.addon
        if not kc:
            layout.label(text="Keyconfig not available")
            return

        for km, kmi in addon_keymaps:
            if km and kmi:
                box = layout.box()
                rna_keymap_ui.draw_kmi(
                    context,
                    kc,
                    km,
                    kmi,
                    box,
                    0
                )


# --------------------------------------------------
# Keymap
# --------------------------------------------------

def register_keymap():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if not kc:
        return

    km = kc.keymaps.new(
        name="Dopesheet",
        space_type='DOPESHEET_EDITOR'
    )

    kmi = km.keymap_items.new(
        ANIM_OT_move_first_frame.bl_idname,
        type='N',
        value='PRESS',
        shift=True
    )

    addon_keymaps.append((km, kmi))


def unregister_keymap():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


# --------------------------------------------------
# Register
# --------------------------------------------------

classes = (
    ANIM_OT_move_first_frame,
    MoveFirstFramePreferences,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    register_keymap()


def unregister():
    unregister_keymap()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
