// This is a basic example of sending (pushing) a data (motion vectors) to a ZMQ socket.
// See 'midi.js' how to receive (pull) them.

import * as zmq from "zmq";

import {
  get_forward_mvs,
} from "../free-for-all/helpers.mjs";

let zpush;

export function setup(args)
{
  args.features = [ "mv" ];

  const ctx = new zmq.Context();
  zpush = ctx.socket(zmq.PUSH);
  zpush.connect("tcp://localhost:5555");
}

export function glitch_frame(frame, stream)
{
  const fwd_mvs = get_forward_mvs(frame, "truncate");
  // bail out if we have no motion vectors
  if ( !fwd_mvs )
    return;

  const data = fwd_mvs.toUint8FFArray();
  zpush.send(data, zmq.DONTWAIT);
}
