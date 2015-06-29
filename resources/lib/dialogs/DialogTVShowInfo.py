# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

import xbmc
import xbmcgui
from ..Utils import *
from ..ImageTools import *
from ..TheMovieDB import *
from ..YouTube import *
from DialogBaseInfo import DialogBaseInfo
from ..WindowManager import wm
from .. import VideoPlayer
PLAYER = VideoPlayer.VideoPlayer()


class DialogTVShowInfo(DialogBaseInfo):

    def __init__(self, *args, **kwargs):
        super(DialogTVShowInfo, self).__init__(*args, **kwargs)
        self.tmdb_id = kwargs.get('tmdb_id', False)
        self.type = "TVShow"
        if not self.tmdb_id:
            notify(LANG(32143))
            return None
        data = extended_tvshow_info(tvshow_id=self.tmdb_id,
                                    dbid=self.dbid)
        if data:
            self.info, self.data, self.account_states = data
        else:
            notify(LANG(32143))
            return None
        youtube_thread = GetYoutubeVidsThread(search_str=self.info['title'] + " tv")
        youtube_thread.start()
        if "dbid" not in self.info:  # need to add comparing for tvshows
            poster_thread = FunctionThread(function=get_file,
                                           param=self.info.get("poster", ""))
            poster_thread.start()
        if "dbid" not in self.info:
            poster_thread.join()
            self.info['poster'] = poster_thread.listitems
        filter_thread = FilterImageThread(image=self.info.get("poster", ""))
        filter_thread.start()
        youtube_thread.join()
        filter_thread.join()
        self.info['ImageFilter'] = filter_thread.image
        self.info['ImageColor'] = filter_thread.imagecolor
        self.listitems = [(150, self.data["similar"]),
                          (250, self.data["seasons"]),
                          (1450, self.data["networks"]),
                          (550, self.data["studios"]),
                          (650, merge_with_cert_desc(self.data["certifications"], "tv")),
                          (750, self.data["crew"]),
                          (850, self.data["genres"]),
                          (950, self.data["keywords"]),
                          (1000, self.data["actors"]),
                          (1150, self.data["videos"]),
                          (1250, self.data["images"]),
                          (1350, self.data["backdrops"]),
                          (350, youtube_thread.listitems)]
        self.listitems = [(a, create_listitems(b)) for a, b in self.listitems]

    def onInit(self):
        super(DialogTVShowInfo, self).onInit()
        pass_dict_to_skin(data=self.info,
                          prefix="movie.",
                          window_id=self.window_id)
        self.fill_lists()
        self.update_states(False)

    def onClick(self, control_id):
        control = self.getControl(control_id)
        if control_id == 120:
            self.close()
            xbmc.executebuiltin("ActivateWindow(videos,videodb://tvshows/titles/%s/)" % (self.dbid))
        elif control_id in [1000, 750]:
            listitem = control.getSelectedItem()
            selection = xbmcgui.Dialog().select(heading=LANG(32151),
                                                list=[LANG(32147), LANG(32009)])
            if selection == 0:
                self.open_credit_dialog(listitem.getProperty("credit_id"))
            if selection == 1:
                wm.open_actor_info(prev_window=self,
                                   actor_id=listitem.getProperty("id"))
        elif control_id in [150]:
            wm.open_tvshow_info(prev_window=self,
                                tvshow_id=control.getSelectedItem().getProperty("id"),
                                dbid=control.getSelectedItem().getProperty("dbid"))
        elif control_id in [250]:
            wm.open_season_info(prev_window=self,
                                tvshow_id=self.tmdb_id,
                                season=control.getSelectedItem().getProperty("season"),
                                tvshow=self.info['title'])
        elif control_id in [350, 1150]:
            PLAYER.play_youtube_video(youtube_id=control.getSelectedItem().getProperty("youtube_id"),
                                      listitem=control.getSelectedItem(),
                                      window=self)
        elif control_id == 550:
            filters = [{"id": control.getSelectedItem().getProperty("id"),
                        "type": "with_companies",
                        "typelabel": LANG(20388),
                        "label": control.getSelectedItem().getLabel().decode("utf-8")}]
            wm.open_video_list(prev_window=self,
                               filters=filters)
        elif control_id == 950:
            filters = [{"id": control.getSelectedItem().getProperty("id"),
                        "type": "with_keywords",
                        "typelabel": LANG(32114),
                        "label": control.getSelectedItem().getLabel().decode("utf-8")}]
            wm.open_video_list(prev_window=self,
                               filters=filters)
        elif control_id == 850:
            filters = [{"id": control.getSelectedItem().getProperty("id"),
                        "type": "with_genres",
                        "typelabel": LANG(135),
                        "label": control.getSelectedItem().getLabel().decode("utf-8")}]
            wm.open_video_list(prev_window=self,
                               filters=filters,
                               media_type="tv")
        elif control_id == 1450:
            filters = [{"id": control.getSelectedItem().getProperty("id"),
                        "type": "with_networks",
                        "typelabel": LANG(32152),
                        "label": control.getSelectedItem().getLabel().decode("utf-8")}]
            wm.open_video_list(prev_window=self,
                               filters=filters,
                               media_type="tv")
        elif control_id in [1250, 1350]:
            wm.open_slideshow(image=control.getSelectedItem().getProperty("original"))
        elif control_id == 445:
            self.show_manage_dialog()
        elif control_id == 6001:
            rating = get_rating_from_user()
            if rating:
                set_rating(media_type="tv",
                           media_id=self.tmdb_id,
                           rating=rating)
                self.update_states()
        elif control_id == 6002:
            listitems = [LANG(32144), LANG(32145)]
            index = xbmcgui.Dialog().select(heading=LANG(32136),
                                            list=listitems)
            if index == -1:
                pass
            elif index == 0:
                wm.open_video_list(prev_window=self,
                                   media_type="tv",
                                   mode="favorites")
            elif index == 1:
                wm.open_video_list(prev_window=self,
                                   mode="rating",
                                   media_type="tv")
        elif control_id == 6003:
            status = str(not bool(self.account_states["favorite"])).lower()
            change_fav_status(media_id=self.info["id"],
                              media_type="tv",
                              status=status)
            self.update_states()
        elif control_id == 6006:
            wm.open_video_list(prev_window=self,
                               mode="rating",
                               media_type="tv")
        elif control_id == 132:
            wm.open_textviewer(header=LANG(32037),
                               text=self.info["Plot"],
                               color=self.info['ImageColor'])

    def update_states(self, force_update=True):
        if force_update:
            xbmc.sleep(2000)  # delay because MovieDB takes some time to update
            _, __, updated_state = extended_tvshow_info(tvshow_id=self.tmdb_id,
                                                        cache_time=0,
                                                        dbid=self.dbid)
            self.account_states = updated_state
        if not self.account_states:
            return None
        if self.account_states["favorite"]:
            self.window.setProperty("FavButton_Label", LANG(32155))
            self.window.setProperty("movie.favorite", "True")
        else:
            self.window.setProperty("FavButton_Label", LANG(32154))
            self.window.setProperty("movie.favorite", "")
        if self.account_states["rated"]:
            self.window.setProperty("movie.rated", str(self.account_states["rated"]["value"]))
        else:
            self.window.setProperty("movie.rated", "")
        self.window.setProperty("movie.watchlist", str(self.account_states["watchlist"]))

    def show_manage_dialog(self):
        manage_list = []
        title = self.info.get("TVShowTitle", "")
        if self.dbid:
            manage_list += [[LANG(413), "RunScript(script.artwork.downloader,mode=gui,mediatype=tv,dbid=" + self.dbid + ")"],
                            [LANG(14061), "RunScript(script.artwork.downloader, mediatype=tv, dbid=" + self.dbid + ")"],
                            [LANG(32101), "RunScript(script.artwork.downloader,mode=custom,mediatype=tv,dbid=" + self.dbid + ",extrathumbs)"],
                            [LANG(32100), "RunScript(script.artwork.downloader,mode=custom,mediatype=tv,dbid=" + self.dbid + ")"]]
        else:
            manage_list += [[LANG(32166), "RunScript(special://home/addons/plugin.program.sickbeard/resources/lib/addshow.py," + title + ")"]]
        # if xbmc.getCondVisibility("system.hasaddon(script.tvtunes)") and self.dbid:
        #     manage_list.append([LANG(32102), "RunScript(script.tvtunes,mode=solo&amp;tvpath=$ESCINFO[Window.Property(movie.FilenameAndPath)]&amp;tvname=$INFO[Window.Property(movie.TVShowTitle)])"])
        if xbmc.getCondVisibility("system.hasaddon(script.libraryeditor)") and self.dbid:
            manage_list.append([LANG(32103), "RunScript(script.libraryeditor,DBID=" + self.dbid + ")"])
        manage_list.append([LANG(1049), "Addon.OpenSettings(script.extendedinfo)"])
        listitems = [item[0] for item in manage_list]
        selection = xbmcgui.Dialog().select(heading=LANG(32133),
                                            list=listitems)
        if selection < 0:
            return None
        builtin_list = manage_list[selection][1].split("||")
        for item in builtin_list:
            xbmc.executebuiltin(item)
