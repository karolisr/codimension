#
# -*- coding: utf-8 -*-
#
# codimension - graphics python two-way code editor and analyzer
# Copyright (C) 2010  Sergey Satskiy <sergey.satskiy@gmail.com>
#
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# $Id$
#

#
# The file was taken from eric 4.4.3 and adopted for codimension.
# Original copyright:
# Copyright (c) 2007 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

" Project browser with module browsing capabilities "

from PyQt4.QtCore        import SIGNAL
from utils.pixmapcache   import PixmapCache
from utils.globals       import GlobalData
from projectbrowsermodel import ProjectBrowserModel
from filesbrowserbase    import FilesBrowser


class ProjectBrowser( FilesBrowser ):
    " Project tree browser "

    def __init__( self, parent = None ):

        FilesBrowser.__init__( self, ProjectBrowserModel(), True, parent )

        self.setWindowTitle( 'Project browser' )
        self.setWindowIcon( PixmapCache().getIcon( 'icon.png' ) )

        self.connect( GlobalData().project, SIGNAL( 'projectChanged' ),
                      self.__onProjectChanged )
        self.connect( GlobalData().project, SIGNAL( 'fsChanged' ),
                      self.__onFSChanged )
        return

    def __onProjectChanged( self, what ):
        " Triggered when a project is changed "
        self.model().reset()
        return

    def __onFSChanged( self, items ):
        " Triggered when the project files set has been changed "
        # It can be far more sofisticated...
        self.model().sourceModel().populateModel()
        self.model().reset()
        self.layoutDisplay()
        return

    def reload( self ):
        " Reloads the projects view "
        self.model().sourceModel().populateModel()
        self.model().reset()
        self.layoutDisplay()
        return
