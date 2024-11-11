// dd_horizontalZoom.js

let zspeed = -15;

export function setup(args)
{
    args.features = [ "mv" ];

    // Pass "-sp <value>" in the command line, where <value> is an
    // integer.
    if ( "params" in args )
        zspeed = args.params;
}

export function glitch_frame(frame)
{
    // bail out if we have no forward motion vectors
    const fwd_mvs = frame.mv?.forward;
    if ( !fwd_mvs )
        return;

    // set motion vector overflow behaviour in ffedit to "truncate"
    frame.mv.overflow = "truncate";

    const MID_POINT = fwd_mvs.width / 2;
    fwd_mvs.forEach((mv, i, j) => {
        if ( j > MID_POINT )
            mv[0] += zspeed;
        else
            mv[0] -= zspeed;
        mv[1] = 0;
    });
}
