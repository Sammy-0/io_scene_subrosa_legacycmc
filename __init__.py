import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper


class ImportCMO(bpy.types.Operator, ImportHelper):
    """Load a Sub Rosa Object File"""

    bl_idname = "import_scene.cmo"
    bl_label = "Import CMO"
    bl_options = {"UNDO"}

    filename_ext = ".cmo"
    filter_glob = StringProperty(default="*.cmo", options={"HIDDEN"})

    def execute(self, context):
        from . import import_cmo

        keywords = self.as_keywords(ignore=("filter_glob",))
        return import_cmo.load(context, **keywords)


class ImportCMC(bpy.types.Operator, ImportHelper):
    """Load a Sub Rosa Character File"""

    bl_idname = "import_scene.cmc"
    bl_label = "Import CMC"
    bl_options = {"UNDO"}

    filename_ext = ".cmc"
    filter_glob = StringProperty(default="*.cmc", options={"HIDDEN"})

    def execute(self, context):
        from . import import_cmc

        keywords = self.as_keywords(ignore=("filter_glob",))
        return import_cmc.load(context, **keywords)

class ImportLegacyCMC(bpy.types.Operator, ImportHelper):
    """Load a Sub Rosa Character File"""

    bl_idname = "import_scene.legacycmc"
    bl_label = "Import Legacy CMC"
    bl_options = {"UNDO"}

    filename_ext = ".cmc"
    filter_glob = StringProperty(default="*.cmc", options={"HIDDEN"})

    def execute(self, context):
        from . import import_legacycmc

        keywords = self.as_keywords(ignore=("filter_glob",))
        return import_legacycmc.load(context, **keywords)


class ImportITM(bpy.types.Operator, ImportHelper):
    """Load a Sub Rosa Item File"""

    bl_idname = "import_scene.itm"
    bl_label = "Import ITM"
    bl_options = {"UNDO"}

    filename_ext = ".itm"
    filter_glob = StringProperty(default="*.itm", options={"HIDDEN"})

    def execute(self, context):
        from . import import_itm

        keywords = self.as_keywords(ignore=("filter_glob",))
        return import_itm.load(context, **keywords)


class ImportSIT(bpy.types.Operator, ImportHelper):
    """Load a Sub Rosa Legacy Item File"""

    bl_idname = "import_scene.sit"
    bl_label = "Import SIT"
    bl_options = {"UNDO"}

    filename_ext = ".sit"
    filter_glob = StringProperty(default="*.sit", options={"HIDDEN"})

    def execute(self, context):
        from . import import_sit

        keywords = self.as_keywords(ignore=("filter_glob",))
        return import_sit.load(context, **keywords)


class ImportSBV(bpy.types.Operator, ImportHelper):
    """Load a Sub Rosa Vehicle File"""

    bl_idname = "import_scene.sbv"
    bl_label = "Import SBV"
    bl_options = {"UNDO"}

    filename_ext = ".sbv"
    filter_glob = StringProperty(default="*.sbv", options={"HIDDEN"})

    def execute(self, context):
        from . import import_sbv

        keywords = self.as_keywords(ignore=("filter_glob",))
        return import_sbv.load(context, **keywords)


def menu_func_import(self, context):
    self.layout.operator(ImportCMO.bl_idname, text="Sub Rosa Object (.cmo)")
    self.layout.operator(ImportCMC.bl_idname, text="Sub Rosa Character (.cmc)")
    self.layout.operator(ImportLegacyCMC.bl_idname, text="Legacy Sub Rosa Character (.cmc)")
    self.layout.operator(ImportITM.bl_idname, text="Sub Rosa Item (.itm)")
    self.layout.operator(ImportSIT.bl_idname, text="Sub Rosa Legacy Item (.sit)")
    self.layout.operator(ImportSBV.bl_idname, text="Sub Rosa Vehicle (.sbv)")


class ExportCMO(bpy.types.Operator, ExportHelper):
    """Export a Sub Rosa Object File"""

    bl_idname = "export_scene.cmo"
    bl_label = "Export CMO"

    filename_ext = ".cmo"
    filter_glob = StringProperty(default="*.cmo", options={"HIDDEN"})

    def execute(self, context):
        from . import export_cmo

        keywords = self.as_keywords(ignore=("filter_glob", "check_existing"))
        return export_cmo.save(context, **keywords)


class ExportCMC(bpy.types.Operator, ExportHelper):
    """Export a Sub Rosa Character File"""

    bl_idname = "export_scene.cmc"
    bl_label = "Export CMC"

    filename_ext = ".cmc"
    filter_glob = StringProperty(default="*.cmc", options={"HIDDEN"})

    def execute(self, context):
        from . import export_cmc

        keywords = self.as_keywords(ignore=("filter_glob", "check_existing"))
        didError, message = export_cmc.save(context, **keywords)
        if didError:
            self.report({"INFO"}, message)
            return {"CANCELLED"}

        return {"FINISHED"}
class ExportLegacyCMC(bpy.types.Operator, ExportHelper):
    """Export a Legacy Sub Rosa Character File"""

    bl_idname = "export_scene.legacycmc"
    bl_label = "Export Legacy CMC"

    filename_ext = ".cmc"
    filter_glob = StringProperty(default="*.cmc", options={"HIDDEN"})

    def execute(self, context):
        from . import export_legacycmc

        keywords = self.as_keywords(ignore=("filter_glob", "check_existing"))
        didError, message = export_legacycmc.save(context, **keywords)
        if didError:
            self.report({"INFO"}, message)
            return {"CANCELLED"}

        return {"FINISHED"}


def menu_func_export(self, context):
    self.layout.operator(ExportCMO.bl_idname, text="Sub Rosa Object (.cmo)")
    self.layout.operator(ExportCMC.bl_idname, text="Sub Rosa Character (.cmc)")
    self.layout.operator(ExportLegacyCMC.bl_idname, text="Legacy Sub Rosa Character (.cmc)")


classes = (ImportCMO, ImportCMC, ImportLegacyCMC, ImportITM, ImportSIT, ImportSBV, ExportCMO, ExportCMC, ExportLegacyCMC)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    for cls in classes:
        bpy.utils.unregister_class(cls)
