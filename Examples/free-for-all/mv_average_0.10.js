// global variable holding forward motion vectors from previous frames
let prev_fwd_mvs = [ ];
let total_sum;

// change this value to use a smaller or greater number of frames to
// perform the average of motion vectors
// you can also change it using the `-sp <num>` command line option
let tail_length = 10;

export function setup(args)
{
    // select motion vector feature
    args.features = [ "mv" ];

    // create a new output filename based on the current time
    // and the input filename
    const date_str = new Date().toISOString().replaceAll(':', '_');
    const output_fname = `glitched_${date_str}`;
    args.output = output_fname;
    console.log(`Output filename is "${output_fname}"`);

    // parse tail_length param from command line if available
    if ( "params" in args )
        tail_length = args.params;
}

export function glitch_frame(frame)
{
    // bail out if we have no forward motion vectors
    const fwd_mvs = frame.mv?.forward;
    if ( !fwd_mvs )
        return;

    // set motion vector overflow behaviour in ffedit to "truncate"
    frame.mv.overflow = "truncate";

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
        fwd_mvs.assign(total_sum);
        fwd_mvs.div(MV(tail_length, tail_length));
    }
}
