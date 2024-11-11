// dd_circular.js

export function setup(args)
{
    args.features = [ "mv" ];
}

export function glitch_frame(frame)
{
    // bail out if we have no forward motion vectors
    const fwd_mvs = frame.mv?.forward;
    if ( !fwd_mvs )
        return;

    // set motion vector overflow behaviour in ffedit to "truncate"
    frame.mv.overflow = "truncate";

    fwd_mvs.forEach((mv, i, j) => {
        mv[0] *= Math.sin(i);
        mv[1] *= Math.cos(j);
    });
}
