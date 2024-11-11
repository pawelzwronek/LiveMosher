export function setup(args)
{
    args.features = ['info', 'mv']; // Select info and motion vectors for glitch_frame

    if ('params' in args) {
        console.log('Parameters:', args.params);
    }
}

export function glitch_frame(frame, stream)
{
    const fnum = frame.frame_num; // Frame number

    console.log(fnum + ':', 'pict_type:', frame.info?.pict_type);

    if (frame.mv) {
        frame.mv.overflow = 'truncate'; // Truncate motion vectors that go out of bounds
        if (frame.mv.forward) {
            frame.mv.forward.sub_v(5); // Subtract 5 from all forward motion vectors
        }
    }
}
