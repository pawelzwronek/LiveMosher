// dd_zoomInOut.js

let ZOOM = 20;

export function setup(args)
{
    args.features = [ "mv" ];

    // Pass "-sp <value>" in the command line, where <value> is an
    // integer.
    if ( "params" in args )
        ZOOM = args.params;
}

export function glitch_frame(frame)
{
    // bail out if we have no forward motion vectors
    const fwd_mvs = frame.mv?.forward;
    if ( !fwd_mvs )
        return;

    // set motion vector overflow behaviour in ffedit to "truncate"
    frame.mv.overflow = "truncate";

    const M_H = fwd_mvs.height / 2;
    const M_W = fwd_mvs.width  / 2;

    fwd_mvs.forEach((mv, i, j) => {
        if ( i > M_H )
        {
            mv[0] += ((M_W - j) / 100) * ZOOM;
            mv[1] += ((M_H - i) / 100) * ZOOM;
        }
        else
        {
            mv[0] -= ((M_W - j) / 100) * ZOOM;
            mv[1] -= ((M_H - i) / 100) * ZOOM;
        }
    });
}
