// dd_antiGravity.js

// global variable holding forward motion vectors from previous frames
let old_mvs;
// a variable for gravity
let gravity = -10;

export function setup(args)
{
    args.features = [ "mv" ];

    // Pass "-sp <value>" in the command line, where <value> is an
    // integer.
    if ( "params" in args )
        gravity = args.params;
}

export function glitch_frame(frame)
{
    // bail out if we have no forward motion vectors
    const fwd_mvs = frame.mv?.forward;
    if ( !fwd_mvs )
        return;

    // set motion vector overflow behaviour in ffedit to "truncate"
    frame.mv.overflow = "truncate";

    // buffer first set of vectors. . .
    if ( !old_mvs )
        old_mvs = fwd_mvs.dup();

    const deep_copy = fwd_mvs.dup();
    const mask = fwd_mvs.compare_lt_v(0);
    fwd_mvs.assign_v(old_mvs, mask);
    old_mvs.add_v(deep_copy, mask);
    old_mvs.sub_v(gravity, mask);
}
