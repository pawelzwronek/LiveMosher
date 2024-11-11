// dd_maxZero.js

// only fuck things up if mv > movement_threshold
let movement_threshold = 10;

export function setup(args)
{
    args.features = [ "mv" ];

    // Pass "-sp <value>" in the command line, where <value> is an
    // integer.
    if ( "params" in args )
        movement_threshold = args.params;
}

export function glitch_frame(frame)
{
    // bail out if we have no forward motion vectors
    const fwd_mvs = frame.mv?.forward;
    if ( !fwd_mvs )
        return;

    // set motion vector overflow behaviour in ffedit to "truncate"
    frame.mv.overflow = "truncate";

    const mask = fwd_mvs.compare_gt(movement_threshold * movement_threshold);
    fwd_mvs.assign(0, 0, mask);
}
