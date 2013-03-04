# layerindex-web - admin interface definitions
#
# Copyright (C) 2013 Intel Corporation
#
# Licensed under the MIT license, see COPYING.MIT for details

from layerindex.models import *
from django.contrib import admin
from reversion_compare.admin import CompareVersionAdmin
from django.forms import TextInput

class LayerMaintainerInline(admin.StackedInline):
    model = LayerMaintainer

class LayerDependencyInline(admin.StackedInline):
    model = LayerDependency

class BranchAdmin(CompareVersionAdmin):
    model = Branch

class LayerItemAdmin(CompareVersionAdmin):
    list_filter = ['status', 'layer_type']
    save_as = True
    search_fields = ['name', 'summary']
    formfield_overrides = {
        models.URLField: {'widget': TextInput(attrs={'size':'100'})},
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
    }

class LayerBranchAdmin(CompareVersionAdmin):
    list_filter = ['layer__name']
    readonly_fields = ['layer', 'branch', 'vcs_last_fetch', 'vcs_last_rev', 'vcs_last_commit']
    inlines = [
        LayerDependencyInline,
        LayerMaintainerInline,
    ]

class LayerMaintainerAdmin(CompareVersionAdmin):
    list_filter = ['status', 'layerbranch__layer__name']

class LayerDependencyAdmin(CompareVersionAdmin):
    list_filter = ['layerbranch__layer__name']

class LayerNoteAdmin(CompareVersionAdmin):
    list_filter = ['layer__name']

class RecipeAdmin(admin.ModelAdmin):
    search_fields = ['filename', 'pn']
    list_filter = ['layerbranch__layer__name', 'layerbranch__branch__name']
    readonly_fields = [fieldname for fieldname in Recipe._meta.get_all_field_names() if fieldname != 'recipefiledependency']
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

class MachineAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_filter = ['layerbranch__layer__name', 'layerbranch__branch__name']
    readonly_fields = Machine._meta.get_all_field_names()
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(Branch, BranchAdmin)
admin.site.register(LayerItem, LayerItemAdmin)
admin.site.register(LayerBranch, LayerBranchAdmin)
admin.site.register(LayerMaintainer, LayerMaintainerAdmin)
admin.site.register(LayerDependency, LayerDependencyAdmin)
admin.site.register(LayerNote, LayerNoteAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(RecipeFileDependency)
admin.site.register(Machine, MachineAdmin)
