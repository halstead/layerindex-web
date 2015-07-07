#!/usr/bin/env python

# Standalone script which rebuilds the history of maintainership
#
# Copyright (C) 2015 Intel Corporation
# Author: Anibal Limon <anibal.limon@linux.intel.com>
#
# Licensed under the MIT license, see COPYING.MIT for details

import sys
import os.path
import optparse
import logging

sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__))))
from common import common_setup, update_repo, get_logger
common_setup()
from layerindex import utils, recipeparse

utils.setup_django()
from django.db import transaction
import settings

from layerindex.models import Recipe, LayerBranch, LayerItem
from rrs.models import Maintainer, RecipeMaintainerHistory, RecipeMaintainer

MAINTAINERS_INCLUDE_PATH = 'meta-yocto/conf/distro/include/maintainers.inc'


"""
    Try to get recipe maintainer from line, if not found return None
"""
def get_recipe_maintainer(line, logger):
    import re
    regex = re.compile('^RECIPE_MAINTAINER_pn-(?P<pn>.*)\s=\s"(?P<name>.+) <(?P<email>.*)>"$')

    match = regex.search(line)
    if match:
        return (match.group('pn'), match.group('name'), match.group('email'))
    else:
        logger.debug("line (%s) don\'t match" % (line))
        return None

"""
    Get commit information from text.
    Returns author_name, author_email, date and title.
"""
def get_commit_info(info, logger):
    import re
    from datetime import datetime
    from email.utils import parsedate_tz, mktime_tz

    author_regex = re.compile("^Author: (?P<name>.*) <(?P<email>.*)>$")
    date_regex = re.compile("^Date:   (?P<date>.*)$")
    title_regex = re.compile("^    (?P<title>.*)$")

    lines = info.split('\n')

    author_name = author_regex.search(lines[1]).group('name')
    author_email = author_regex.search(lines[1]).group('email')
    date_str = date_regex.search(lines[2]).group('date')
    date = datetime.utcfromtimestamp(mktime_tz(parsedate_tz(date_str)))
    title = title_regex.search(lines[4]).group('title')

    return (author_name, author_email, date, title)

"""
    Recreate Maintainership history from the beign of Yocto Project
"""
def maintainer_history(logger):
    layername = settings.CORE_LAYER_NAME
    branchname = "master"

    layer = LayerItem.objects.filter(name__iexact = layername)[0]
    if not layer:
        logger.error("Core layer does not exist, please add into settings.")
        sys.exit(1)
    urldir = layer.get_fetch_dir()
    layerbranch = LayerBranch.objects.filter(layer__name__iexact =
                        layername).filter(branch__name__iexact =
                        branchname)[0]
    repodir = os.path.join(settings.LAYER_FETCH_DIR, urldir)
    layerdir = os.path.join(repodir, layerbranch.vcs_subdir)

    pokypath = update_repo(settings.LAYER_FETCH_DIR, 'poky', settings.POKY_REPO_URL,
        True, logger)
    utils.runcmd("git checkout master -f", pokypath, logger=logger)
    maintainers_full_path = os.path.join(pokypath, MAINTAINERS_INCLUDE_PATH)

    commits = utils.runcmd("git log --format='%H' --reverse --date=rfc " +
            MAINTAINERS_INCLUDE_PATH, pokypath, logger=logger)

    transaction.enter_transaction_management()
    transaction.managed(True)
    for commit in commits.strip().split("\n"):
        if RecipeMaintainerHistory.objects.filter(sha1=commit):
            continue

        logger.debug("Analysing commit %s ..." % (commit))

        (author_name, author_email, date, title) = \
            get_commit_info(utils.runcmd("git show " + commit, pokypath,
                logger=logger), logger)

        author = Maintainer.create_or_update(author_name, author_email)
        rms = RecipeMaintainerHistory(title=title, date=date, author=author,
                sha1=commit)
        rms.save()
        
        branchname = 'maintainer' + commit 
        utils.runcmd("git checkout %s -b %s -f" % (commit, branchname),
                pokypath, logger=logger)

        lines = [line.strip() for line in open(maintainers_full_path)]
        for line in lines:
            res = get_recipe_maintainer(line, logger)
            if res:
                (pn, name, email) = res
                qry = Recipe.objects.filter(pn = pn, layerbranch = layerbranch)

                if qry:
                    m = Maintainer.create_or_update(name, email)

                    rm = RecipeMaintainer()
                    rm.recipe = qry[0]
                    rm.maintainer = m
                    rm.history = rms
                    rm.save()

                    logger.debug("%s: Change maintainer to %s in commit %s." % \
                            (pn, m.name, commit))
                else:
                    logger.debug("%s: Not found in layer %s." % \
                            (pn, layername))

        # set missing recipes to no maintainer
        m = Maintainer.objects.get(id = 0) # No Maintainer
        for recipe in Recipe.objects.all():
            if not RecipeMaintainer.objects.filter(recipe = recipe, history = rms):
                rm = RecipeMaintainer()
                rm.recipe = recipe
                rm.maintainer = m
                rm.history = rms
                rm.save()
                logger.debug("%s: Not found maintainer in commit %s set to 'No maintainer'." % \
                                (recipe.pn, rms.sha1))

        utils.runcmd("git checkout master -f", pokypath, logger=logger)
        utils.runcmd("git branch -D %s" % (branchname), pokypath, logger=logger)

    transaction.commit()
    transaction.leave_transaction_management()

if __name__=="__main__":
    parser = optparse.OptionParser(usage = """%prog [options]""")
    
    parser.add_option("-d", "--debug",
            help = "Enable debug output",
            action="store_const", const=logging.DEBUG, dest="loglevel",
            default=logging.INFO)
    
    logger = get_logger("MaintainerUpdate", settings)
    options, args = parser.parse_args(sys.argv)
    logger.setLevel(options.loglevel)

    maintainer_history(logger)