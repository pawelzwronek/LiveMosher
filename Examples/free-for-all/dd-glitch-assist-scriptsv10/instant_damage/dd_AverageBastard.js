// dd_AverageBastard

// global variable holding forward motion vectors from previous frames
let prev_average_mvs;
let average_mv_sum = new MV(0, 0);

// change this value to use a smaller or greater number of frames to
// perform the average of motion vectors
// you can also change it using the `-sp <num>` command line option
let tail_length = 20;

export function setup(args)
{
    args.features = [ "mv" ];

    // Pass "-sp <value>" in the command line, where <value> is an
    // integer from 0 to 100.
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

    let average_mv = new MV(0, 0);
    fwd_mvs.forEach((mv) => {
        average_mv[0] += mv[0];
        average_mv[1] += mv[1];
    });
    const length = fwd_mvs.height * fwd_mvs.width;
    average_mv[0] = Math.floor(average_mv[0] / length);
    average_mv[1] = Math.floor(average_mv[1] / length);

    if ( !prev_average_mvs )
        prev_average_mvs = Array(tail_length - 1).fill(MV(0, 0));

    // push to the end of array
    prev_average_mvs.push(average_mv);

    // update average_mv_sum by removing the motion vector values from
    // the oldest frame and adding the values from the current frame.
    if ( prev_average_mvs.length > tail_length )
    {
        average_mv_sum.sub(prev_average_mvs[0]);
        prev_average_mvs = prev_average_mvs.slice(1);
    }
    average_mv_sum.add(average_mv);

    // set new values for current frame to (average_mv_sum / tail_length)
    if ( prev_average_mvs.length == tail_length )
    {
        const deep_copy = fwd_mvs.dup();
        fwd_mvs.assign(average_mv_sum);
        fwd_mvs.div(MV(tail_length, tail_length));
        fwd_mvs.add(deep_copy);
    }
}
