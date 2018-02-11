#!/usr/bin/env python3

# Import other distro information
#
# Copyright (C) 2013, 2018 Intel Corporation
# Author: Paul Eggleton <paul.eggleton@linux.intel.com>
#
# Licensed under the MIT license, see COPYING.MIT for details


import sys
import os
import argparse
import logging
from datetime import datetime
import fnmatch
import re
import tempfile
import shutil
from distutils.version import LooseVersion

sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

import utils
import recipeparse

logger = utils.logger_create('LayerIndexOtherDistro')


class DryRunRollbackException(Exception):
    pass


def update_recipe_file(path, recipe, repodir):
    from layerindex.models import Patch, Source
    from django.db import DatabaseError

    try:
        logger.debug('Updating recipe %s' % path)
        recipe.pn = os.path.splitext(recipe.filename)[0]
        with open(path, 'r', errors='surrogateescape') as f:
            indesc = False
            desc = []
            patches = []
            sources = []
            for line in f:
                if line.startswith('%package'):
                    break
                if line.strip() == '%description':
                    indesc = True
                    continue
                if indesc:
                    if line.startswith('%'):
                        indesc = False
                    else:
                        desc.append(line)

                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.rstrip()
                    value = value.strip()
                    if key == 'Version':
                        recipe.pv = value
                    elif key == 'Summary':
                        recipe.summary = value.strip('"\'')
                    elif key == 'Group':
                        recipe.section = value
                    elif key == 'Url':
                        recipe.homepage = value
                    elif key == 'License':
                        recipe.license = value
                    elif key.startswith('Patch'):
                        patches.append(value)
                    elif key.startswith('Source'):
                        sources.append(value)
        recipe.description = ' '.join(desc)
        recipe.save()

        saved_patches = []
        for patchfn in patches:
            patchpath = os.path.join(os.path.relpath(os.path.dirname(path), repodir), patchfn)
            patch, _ = Patch.objects.get_or_create(recipe=recipe, path=patchpath)
            patch.src_path = patchfn
            patch.save()
            saved_patches.append(patch.id)
        recipe.patch_set.exclude(id__in=saved_patches).delete()

        existing_ids = list(recipe.source_set.values_list('id', flat=True))
        for src in sources:
            srcobj, _ = Source.objects.get_or_create(recipe=recipe, url=src)
            srcobj.save()
            if srcobj.id in existing_ids:
                existing_ids.remove(srcobj.id)
        # Need to delete like this because some spec files have a lot of sources!
        for idv in existing_ids:
            Source.objects.filter(id=idv).delete()
    except DatabaseError:
        raise
    except KeyboardInterrupt:
        raise
    except BaseException as e:
        if not recipe.pn:
            recipe.pn = recipe.filename[:-3].split('_')[0]
        logger.error("Unable to read %s: %s", path, str(e))


def check_branch_layer(args):
    from layerindex.models import LayerItem, LayerBranch

    branch = utils.get_branch(args.branch)
    if not branch:
        logger.error("Specified branch %s is not valid" % args.branch)
        return 1, None

    res = list(LayerItem.objects.filter(name=args.layer)[:1])
    if res:
        layer = res[0]
    else:
        logger.error('Cannot find specified layer "%s"' % args.layer)
        return 1, None

    layerbranch = layer.get_layerbranch(args.branch)
    if not layerbranch:
        # LayerBranch doesn't exist for this branch, create it
        layerbranch = LayerBranch()
        layerbranch.layer = layer
        layerbranch.branch = branch
        layerbranch.save()

    return 0, layerbranch


def import_pkgspec(args):
    utils.setup_django()
    import settings
    from layerindex.models import LayerItem, LayerBranch, Recipe, ClassicRecipe, Machine, BBAppend, BBClass
    from django.db import transaction

    ret, layerbranch = check_branch_layer(args)
    if ret:
        return ret

    metapath = args.pkgdir

    try:
        with transaction.atomic():
            layerrecipes = ClassicRecipe.objects.filter(layerbranch=layerbranch)
            existing = list(layerrecipes.filter(deleted=False).values_list('pn', flat=True))
            for entry in os.listdir(metapath):
                specfile = os.path.join(metapath, entry, '%s.spec' % entry)
                if os.path.exists(specfile):
                    recipe, created = ClassicRecipe.objects.get_or_create(layerbranch=layerbranch, pn=entry)
                    if created:
                        logger.info('Importing %s' % os.path.basename(specfile))
                    elif recipe.deleted:
                        logger.info('Restoring and updating %s' % os.path.basename(specfile))
                        recipe.deleted = False
                    else:
                        logger.info('Updating %s' % os.path.basename(specfile))
                    recipe.layerbranch = layerbranch
                    recipe.filename = os.path.basename(specfile)
                    recipe.filepath = os.path.relpath(os.path.dirname(specfile), metapath)
                    update_recipe_file(specfile, recipe, metapath)
                    recipe.save()
                    if entry in existing:
                        existing.remove(entry)
                else:
                    logger.warn('Missing spec file in %s' % os.path.join(metapath, entry))

            if existing:
                logger.info('Marking as deleted: %s' % ', '.join(existing))
                layerrecipes.filter(pn__in=existing).update(deleted=True)

            layerbranch.vcs_last_fetch = datetime.now()
            layerbranch.save()

            if args.dry_run:
                raise DryRunRollbackException()
    except DryRunRollbackException:
        pass
    except:
        import traceback
        traceback.print_exc()
        return 1

    return 0


def import_deblist(args):
    utils.setup_django()
    import settings
    from layerindex.models import LayerItem, LayerBranch, Recipe, ClassicRecipe, Machine, BBAppend, BBClass
    from django.db import transaction

    ret, layerbranch = check_branch_layer(args)
    if ret:
        return ret

    try:
        with transaction.atomic():
            layerrecipes = ClassicRecipe.objects.filter(layerbranch=layerbranch)
            existing = list(layerrecipes.filter(deleted=False).values_list('pn', flat=True))

            def handle_pkg(pkg):
                pkgname = pkg['Package']
                recipe, created = ClassicRecipe.objects.get_or_create(layerbranch=layerbranch, pn=pkgname)
                if created:
                    logger.info('Importing %s' % pkgname)
                elif recipe.deleted:
                    logger.info('Restoring and updating %s' % pkgname)
                    recipe.deleted = False
                else:
                    logger.info('Updating %s' % pkgname)
                filename = pkg.get('Filename', '')
                if filename:
                    recipe.filename = os.path.basename(filename)
                    recipe.filepath = os.path.dirname(filename)
                recipe.section = pkg.get('Section', '')
                description = pkg.get('Description', '')
                if description:
                    description = description.splitlines()
                    recipe.summary = description.pop(0)
                    recipe.description = ' '.join(description)
                recipe.pv = pkg.get('Version', '')
                recipe.homepage = pkg.get('Homepage', '')
                recipe.license = pkg.get('License', '')
                recipe.save()
                if pkgname in existing:
                    existing.remove(pkgname)

            pkgs = []
            pkginfo = {}
            lastfield = ''
            with open(args.pkglistfile, 'r') as f:
                for line in f:
                    linesplit = line.split()
                    if line.startswith('Package:'):
                        # Next package starting, deal with the last one (unless this is the first)
                        if pkginfo:
                            handle_pkg(pkginfo)

                        pkginfo = {}
                        lastfield = 'Package'

                    if line.startswith(' '):
                        if lastfield:
                            pkginfo[lastfield] += '\n' + line.strip()
                    elif ':' in line:
                        field, value = line.split(':', 1)
                        pkginfo[field] = value.strip()
                        lastfield = field
                    else:
                        lastfield = ''
                if pkginfo:
                    # Handle last package
                    handle_pkg(pkginfo)

                if existing:
                    logger.info('Marking as deleted: %s' % ', '.join(existing))
                    layerrecipes.filter(pn__in=existing).update(deleted=True)

                layerbranch.vcs_last_fetch = datetime.now()
                layerbranch.save()

                if args.dry_run:
                    raise DryRunRollbackException()
    except DryRunRollbackException:
        pass
    except:
        import traceback
        traceback.print_exc()
        return 1


def main():

    parser = argparse.ArgumentParser(description='OE Layer Index other distro comparison import tool',
                                        epilog='Use %(prog)s <subcommand> --help to get help on a specific command')
    parser.add_argument('-d', '--debug', help='Enable debug output', action='store_const', const=logging.DEBUG, dest='loglevel', default=logging.INFO)
    parser.add_argument('-q', '--quiet', help='Hide all output except error messages', action='store_const', const=logging.ERROR, dest='loglevel')

    subparsers = parser.add_subparsers(title='subcommands', metavar='<subcommand>')
    subparsers.required = True

    parser_pkgspec = subparsers.add_parser('import-pkgspec',
                                           help='Import from a local rpm-based distro package directory',
                                           description='Imports from a local directory containing subdirectories, each of which contains an RPM .spec file for a package')
    parser_pkgspec.add_argument('branch', help='Branch to import into')
    parser_pkgspec.add_argument('layer', help='Layer to import into')
    parser_pkgspec.add_argument('pkgdir', help='Top level directory containing package subdirectories')
    parser_pkgspec.add_argument('-n', '--dry-run', help='Don\'t write any data back to the database', action='store_true')
    parser_pkgspec.set_defaults(func=import_pkgspec)

    parser_deblist = subparsers.add_parser('import-deblist',
                                           help='Import from a list of Debian packages',
                                           description='Imports from a list of Debian packages')
    parser_deblist.add_argument('branch', help='Branch to import into')
    parser_deblist.add_argument('layer', help='Layer to import into')
    parser_deblist.add_argument('pkglistfile', help='File containing a list of packages, as produced by: apt-cache show "*"')
    parser_deblist.add_argument('-n', '--dry-run', help='Don\'t write any data back to the database', action='store_true')
    parser_deblist.set_defaults(func=import_deblist)


    args = parser.parse_args()

    logger.setLevel(args.loglevel)

    ret = args.func(args)

    return ret

if __name__ == "__main__":
    main()
