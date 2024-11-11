// dd_onlyRise.js
// only let's y-dimension mv's through if they're rising

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

    const mask = fwd_mvs.compare_lt_v(0);
    fwd_mvs.assign_v(0, mask);
}
