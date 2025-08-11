from collections.abc import Callable

from mdcx.config.models import Website

from . import (
    airav,
    airav_cc,
    avsex,
    avsox,
    cableav,
    cnmdb,
    dahlia,
    dmm,
    faleno,
    fantastica,
    fc2,
    fc2club,
    fc2hub,
    fc2ppvdb,
    freejavbt,
    getchu,
    getchu_dmm,
    giga,
    hdouban,
    hscangku,
    iqqtv_new,
    jav321,
    javbus,
    javday,
    javdb,
    javlibrary_new,
    kin8,
    love6,
    lulubar,
    madouqu,
    mdtv,
    mgstage,
    mmtv,
    mywife,
    official,
    prestige,
    theporndb,
    xcity,
)
from .base import get_crawler, register_crawler
from .base.compat import get_v1_crawler, register_v1_crawler
from .dmm_new import DmmCrawler

CRAWLER_FUNCS: list[tuple[Website, Callable]] = [
    (Website.MMTV, mmtv.main),
    (Website.AIRAV_CC, airav_cc.main),  # lang
    (Website.AIRAV, airav.main),  # lang
    (Website.AVSEX, avsex.main),
    (Website.AVSOX, avsox.main),
    (Website.CABLEAV, cableav.main),
    (Website.CNMDB, cnmdb.main),
    (Website.DAHLIA, dahlia.main),
    (Website.DMM, dmm.main),
    (Website.FALENO, faleno.main),
    (Website.FANTASTICA, fantastica.main),
    (Website.FC2, fc2.main),
    (Website.FC2CLUB, fc2club.main),
    (Website.FC2HUB, fc2hub.main),
    (Website.FC2PPVDB, fc2ppvdb.main),
    (Website.FREEJAVBT, freejavbt.main),
    (Website.GETCHU_DMM, getchu_dmm.main),
    (Website.GETCHU, getchu.main),
    (Website.GIGA, giga.main),
    (Website.HDOUBAN, hdouban.main),
    (Website.HSCANGKU, hscangku.main),
    (Website.IQQTV, iqqtv_new.main),  # lang
    (Website.JAV321, jav321.main),
    (Website.JAVBUS, javbus.main),
    (Website.JAVDAY, javday.main),
    (Website.JAVDB, javdb.main),
    (Website.JAVLIBRARY, javlibrary_new.main),  # lang
    (Website.KIN8, kin8.main),
    (Website.LOVE6, love6.main),
    (Website.LULUBAR, lulubar.main),
    (Website.MADOUQU, madouqu.main),
    (Website.MDTV, mdtv.main),
    (Website.MGSTAGE, mgstage.main),
    (Website.MYWIFE, mywife.main),
    (Website.OFFICIAL, official.main),
    (Website.PRESTIGE, prestige.main),
    (Website.THEPORNDB, theporndb.main),
    (Website.XCITY, xcity.main),
]


register_crawler(DmmCrawler)
for site, func in CRAWLER_FUNCS:
    register_v1_crawler(site, func)


def get_crawler_compat(site: Website):
    c = get_crawler(site)
    if c is not None:
        return c
    return get_v1_crawler(site)
