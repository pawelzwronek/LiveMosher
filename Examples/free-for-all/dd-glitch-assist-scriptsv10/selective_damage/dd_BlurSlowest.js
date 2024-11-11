// dd_blurSlowest.js
// apply 20-frame average to the slowest moving mv's
var SOME_PERCENTAGE = 0.10; // only the slowest % of mv's in each frame get glitched

// global variable holding forward motion vectors from previous frames
let prev_fwd_mvs = [ ];
let total_sum;

// change this value to use a smaller or greater number of frmes to average
var tail_length = 20;

export function setup(args)
{
    args.features = [ "mv" ];

    // Pass "-sp <value>" in the command line, where <value> is an
    // integer from 0 to 100.
    if ( "params" in args )
        SOME_PERCENTAGE = (100 - args.params) / 100;
}

export function glitch_frame(frame)
{
    // bail out if we have no forward motion vectors
    const fwd_mvs = frame.mv?.forward;
    if ( !fwd_mvs )
        return;

    // set motion vector overflow behaviour in ffedit to "truncate"
    frame.mv.overflow = "truncate";

    const largest = fwd_mvs.largest_sq();
    const threshold = Math.floor(SOME_PERCENTAGE * largest[2]);
    const mask = fwd_mvs.compare_lt(threshold);

    // update variable holding forward motion vectors from previous
    // frames. note that we perform a deep copy of the clean motion
    // vector values before modifying them.
    const deep_copy = fwd_mvs.dup();
    // push to the end of array
    prev_fwd_mvs.push(deep_copy);

    // initialize total_sum to a [0,0] MV2DArray.
    if ( !total_sum )
        total_sum = new MV2DArray(fwd_mvs.width, fwd_mvs.height);

    // update total_sum by removing the motion vector values from the
    // oldest frame and adding the values from the current frame.
    if ( prev_fwd_mvs.length > tail_length )
    {
        total_sum.sub(prev_fwd_mvs[0]);
        prev_fwd_mvs = prev_fwd_mvs.slice(1);
    }
    total_sum.add(deep_copy);

    // set new values for current frame to (total_sum / tail_length)
    if ( prev_fwd_mvs.length == tail_length )
    {
        fwd_mvs.assign(total_sum, mask);
        fwd_mvs.div(MV(tail_length, tail_length), mask);
    }
}
