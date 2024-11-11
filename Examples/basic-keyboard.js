import { SDL_Codes as Code } from './sdl_codes.js';
const sdl = new SDL();

const cur_pan_mv = new MV(0, 0);

export function setup(args)
{
    args.features = ['info', 'mv']; // Select info and motion vectors for glitch_frame

    if ('params' in args) {
        console.log('Parameters:', args.params);
    }
}

export function glitch_frame(frame, stream)
{
    // Make sure preview window is focused when pressing keys

    const fwd_mvs = frame.mv?.forward;
    if (!fwd_mvs) return;

    let event = null;
    do {
        event = sdl.getEvent();
        if (event?.type === SDL.SDL_KEYDOWN) {
            const code = event.keysym.scancode;
            switch (code) {
                case Code.LEFT: // left arrow
                    cur_pan_mv[0] -= 5; // subtract 5 from x component of motion vector
                    break;
                case Code.RIGHT: // right arrow
                    cur_pan_mv[0] += 5; // add 5 to x component of motion vector
                    break;
                case Code.UP: // up arrow
                    cur_pan_mv[1] -= 5; // subtract 5 from y component of motion vector
                    break;
                case Code.DOWN: // down arrow
                    cur_pan_mv[1] += 5; // add 5 to y component of motion vector
                    break;
            }
            console.log(`cur_pan_mv: ${cur_pan_mv}`);
        }
    } while (event);

    fwd_mvs.add(cur_pan_mv); // pan entire frame with current MV
}
