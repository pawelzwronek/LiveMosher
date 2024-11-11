// dd_circle.js

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

    const H = fwd_mvs.height;
    const W = fwd_mvs.width;
    fwd_mvs.forEach((mv, i, j) => {
        mv[0] *= Math.sin(i / H * Math.PI * 2);
        mv[1] *= Math.cos(j / W * Math.PI * 2);
    });
}
