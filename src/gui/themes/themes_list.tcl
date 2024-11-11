
set theme_dir $vTcl(VTCL_HOME)
set themes {
	clearlooks
	cornsilk-dark
	cornsilk-light
	notsodark
	page-dark
	page-legacy
	page-light
	page-notsodark
	page-wheat
	waldorf
}

foreach theme $themes {
	set filename [file join $theme_dir themes $theme.tcl]
	catch {source $filename}
}
	
