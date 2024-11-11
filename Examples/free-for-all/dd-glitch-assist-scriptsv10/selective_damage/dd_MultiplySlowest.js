// dd_MultiplySlowest.js
// Multiply slowest moving mv's
var LARGEST = 0;
var SOME_PERCENTAGE = 0.10;
var MULTIPLE = 10;

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

    fwd_mvs.mul(MV(MULTIPLE, MULTIPLE), mask);
}
