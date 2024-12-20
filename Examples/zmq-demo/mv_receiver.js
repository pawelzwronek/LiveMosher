// This is a basic example of sending (with request for a response) a data (1 random byte) to a ZMQ socket.
// After sending the data, it checks if there is a response and logs the length of the received data.

import * as zmq from "zmq";

import {
  get_forward_mvs,
} from "../free-for-all/helpers.mjs";

let zreq;

export function setup(args)
{
  args.features = [ "mv" ];

  const ctx = new zmq.Context();
  zreq = ctx.socket(zmq.REQ);
  zreq.connect("tcp://localhost:5556");
}

let request_sent = false;
export function glitch_frame(frame, stream)
{
  const fwd_mvs = get_forward_mvs(frame, "truncate");
  // bail out if we have no motion vectors
  if ( !fwd_mvs )
    return;

  if ( !request_sent )
  {
    const data = new Uint8FFArray(1); // the content doesn't matter
    zreq.send(data, zmq.DONTWAIT);
    request_sent = true;
  }

  const data = zreq.recv(zreq, zmq.DONTWAIT);
  if ( data ) {
    console.log(`received ${data.length} bytes`);
    fwd_mvs.assign(new MV2DArray(data));
    request_sent = false;
  }
}
