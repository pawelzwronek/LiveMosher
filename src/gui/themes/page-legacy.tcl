#
# "page-legacy" theme.
# -------------------------------
# A simple theme originally created for users of PAGE
# -------------------------------
# Inspired by the default theme
# Written by G.D. Walters
# Copyright 2022,2023 by G.D. Walters  <thedesignatedgeek@gmail.com>
#
#==================================================================
# Version 0.1.22
# December 26, 2023
#==================================================================
# Version 0.1.22 - GDW - December 26, 2021
# -----------------------------------------------------------------
#   Changed TCombobutton arrow color to black arrow size to 14
#   Changed TRadiobutton arrow color to black arrow size to 11
#   Reverted TButton style to non-white border and focus
# =================================================================

package require Tk 8.6


namespace eval ttk::theme::page-legacy {
    variable version 0.1.22
    package provide ttk::theme::page-legacy $version    
    variable colors
    array set colors {
    -frame          "#d9d9d9"
    -foreground     "#000000"
    -window         "#ffffff"
    -text           "#000000"
    -activebg       "#d9d9d9"
    -activefg       black
    -selectbg       "#4a6984"
    -selectfg       "#ffffff"
    -darker         "#c3c3c3"
    -disabledfg     "#a3a3a3"
    -indicator      "#4a6984"
    -disabledindicator  "#a3a3a3"
    -altindicator       "#9fbdd8"
    -disabledaltindicator   "#c0c0c0"
    }

    # Get bg and fg colors specified in the preferences.
    catch {
        set ::xframe $::vTcl(actual_gui_bg)
        set ::xfore $::vTcl(actual_gui_fg)
        set ::xfont $::vTcl(actual_gui_font_dft_desc)
        set ::_fgcolor $::vTcl(actual_gui_fg)
        set ::_tabfg1 $::vTcl(tabfg1)
        set ::_tabfg2 $::vTcl(tabfg2)
        set ::_tabbg1 $::vTcl(tabbg1)
        set ::_tabbg2 $::vTcl(tabbg2)
        set ::_bgmode $::vTcl(bg_mode)
    }
	set colors(-frame) $::xframe
	set colors(-foreground) $::xfore	
	
    ttk::style theme create page-legacy -parent clam -settings {

    ttk::style configure "." \
        -borderwidth    1 \
        -background     $colors(-frame) \
        -foreground     $colors(-foreground) \
        -troughcolor    $colors(-darker) \
        -selectborderwidth  1 \
        -selectbackground   $colors(-selectbg) \
        -selectforeground   $colors(-selectfg) \
        -highlightcolor gray66 \
         -font           TkDefaultFont 
        ;
        #-font           $::xfont 
    ttk::style map "." -background \
        [list disabled $colors(-frame)  active $colors(-activebg)]
    ttk::style map "." -foreground \
        [list disabled $colors(-disabledfg)  active $colors(-activefg)]
    
    #     TNotebook
	if {$::_bgmode eq "dark"} {	
    ttk::style configure TNotebook \
        -padding {4 2} -background $colors(-frame) \
        -bordercolor white -darkcolor white -lightcolor black \
		-focuscolor white -focusthickness 2
    }       
#puts "::_tabfg1 = $::_tabfg1"
#puts "::_tabfg2 = $::_tabfg2"
#puts "::_tabbg1 = $::_tabbg1"
#puts "::_tabbg2 = $::_tabbg2"
#puts "::_bgmode = $::_bgmode"
#puts ""	
	# ::_tabbg2 is the complement of
    ttk::style map TNotebook.Tab -background \
        [list selected $::xframe active $::_tabbg1 !active $::_tabbg2]
    ttk::style map TNotebook.Tab -foreground \
            [list selected $::xfore active $::_tabfg1 !active $::_tabfg2]

    ttk::style configure Tab_ne.TNotebook -tabposition "ne"
    ttk::style configure Tab_nw.TNotebook -tabposition "nw"
    ttk::style configure Tab_n.TNotebook -tabposition "n"
    ttk::style configure Tab_en.TNotebook -tabposition "en"
    ttk::style configure Tab_e.TNotebook -tabposition "e"
    ttk::style configure Tab_es.TNotebook -tabposition "es"
    ttk::style configure Tab_sw.TNotebook -tabposition "sw"
    ttk::style configure Tab_s.TNotebook -tabposition "s"
    ttk::style configure Tab_se.TNotebook -tabposition "se"
    ttk::style configure Tab_wn.TNotebook -tabposition "wn"
    ttk::style configure Tab_w.TNotebook -tabposition "w"
    ttk::style configure Tab_ws.TNotebook -tabposition "ws"            

    #     TButton
    ttk::style configure TButton \
        -anchor center -width -11 -padding "1 1" -relief raised \
        -shiftrelief 2 -highlightthickness 1 -highlightcolor $colors(-frame)    
    #ttk::style configure TButton \
        -anchor center -padding "3 3" -width -9 \
        -relief raised -shiftrelief 1 -bordercolor white \
        -darkcolor white -lightcolor white -focuscolor white
    ttk::style map TButton -relief [list {!disabled pressed} sunken]

    #     TCheckbutton
    ttk::style configure TCheckbutton \
        -indicatorcolor "#ffffff" -indicatorrelief sunken -padding 1
    ttk::style map TCheckbutton -indicatorcolor \
        [list pressed $colors(-activebg)  \
            {!disabled alternate} $colors(-altindicator) \
            {disabled alternate} $colors(-disabledaltindicator) \
            {!disabled selected} $colors(-indicator) \
            {disabled selected} $colors(-disabledindicator)]
    ttk::style map TCheckbutton -indicatorrelief \
        [list alternate raised]

    #     TRadiobutton
    ttk::style configure TRadiobutton \
        -indicatorcolor "#ffffff" -indicatorrelief sunken -padding 1
    ttk::style map TRadiobutton -indicatorcolor \
        [list pressed $colors(-activebg)  \
            {!disabled alternate} $colors(-altindicator) \
            {disabled alternate} $colors(-disabledaltindicator) \
            {!disabled selected} $colors(-indicator) \
            {disabled selected} $colors(-disabledindicator)]
    ttk::style map TRadiobutton -indicatorrelief \
        [list alternate raised]

    #     TMenubutton
    ttk::style configure TMenubutton \
        -relief raised -padding "10 3"

    #     TEntry
    ttk::style configure TEntry \
        -relief sunken -fieldbackground white -padding 1 -foreground black
    ttk::style map TEntry \
        -background [list  readonly $colors(-frame)] \
        -foreground [list  readonly black]         
    #ttk::style map TEntry -fieldbackground \
        [list readonly $colors(-frame) disabled $colors(-frame)]

    #     TCombobox
    ttk::style configure TCombobox -arrowsize 14 -padding 1 \
        -arrowcolor black -foreground black
    ttk::style map TCombobox -fieldbackground \
        [list readonly $colors(-frame) disabled $colors(-frame)] \
        -arrowcolor [list disabled $colors(-disabledfg)]

    #     TSpinbox
    ttk::style configure TSpinbox -arrowsize 11 -padding {2 0 10 0} \
        -arrowcolor black -foreground black
    ttk::style map TSpinbox -fieldbackground \
        [list readonly $colors(-frame) disabled $colors(-frame)] \
        -arrowcolor [list disabled $colors(-disabledfg)]

    #     TLabelframe
    ttk::style configure TLabelframe \
        -relief groove -borderwidth 2

    #     TScrollbar
    ttk::style configure TScrollbar \
        -width 12 -arrowsize 12
    ttk::style map TScrollbar \
        -arrowcolor [list disabled $colors(-disabledfg)]

    #     TScale
    ttk::style configure TScale \
        -sliderrelief raised
    ttk::style configure TProgressbar \
        -background $colors(-selectbg)

    # Treeview.
    #
    ttk::style configure Heading -font TkHeadingFont -relief raised
    ttk::style configure Treeview \
        -background $colors(-window) \
        -foreground $colors(-text) ;
    ttk::style map Treeview \
        -background [list disabled $colors(-frame)\
                selected $colors(-selectbg)] \
        -foreground [list disabled $colors(-disabledfg) \
                selected $colors(-selectfg)]

    # Combobox popdown frame
    ttk::style layout ComboboxPopdownFrame {
        ComboboxPopdownFrame.border -sticky nswe
    }
    ttk::style configure ComboboxPopdownFrame \
        -borderwidth 1 -relief solid

    #
    # Toolbar buttons:
    #
    ttk::style layout Toolbutton {
        Toolbutton.border -children {
        Toolbutton.padding -children {
            Toolbutton.label
        }
        }
    }

    ttk::style configure Toolbutton \
        -padding 2 -relief flat
    ttk::style map Toolbutton -relief \
        [list disabled flat selected sunken pressed sunken active raised]
    ttk::style map Toolbutton -background \
        [list pressed $colors(-darker)  active $colors(-activebg)]
}   
}
