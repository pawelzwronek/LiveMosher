export class MIDIInput
{
  constructor()
  {
    this.midiin = new RtMidiIn();
    this.midiout = new RtMidiOut();
    this.events = {};
    this.buttons = {};
    this.log = false;
  }

  setup(arg)
  {
    let port_name;
    let port_num;
    let midiin = this.midiin;
    const repeater_name = "RtMidi Repeater";
    let is_repeater = false;

    // Check arguments
    if ( arg !== undefined )
    {
      if ( typeof arg === 'string' )
        port_name = arg;
      else
        port_num = arg;
    }

    // Check if any MIDI ports are available
    const count = midiin.getPortCount();
    let portS = "s";
    if ( count === 1 )
      portS = "";
    console.log("RtMidi: " + count + " port" + portS + " found");
    if ( count === 0 )
      throw "No MIDI ports";

    // Print names and select port number
    for ( let i = 0; i < count; i++ )
    {
      const name = midiin.getPortName(i);
      if ( name == port_name )
        port_num = i;
      console.log(i + ". " + name);
    }

    // Sanity check for port name
    if ( port_name !== undefined && port_num === undefined )
    {
      console.log("Selected port name (" + port_name + ") is not available.");
      throw "Bad MIDI port name";
    }

    // Sanity check for port number
    if ( port_num >= count )
    {
      printf("Selected port number (" + port_num + ") greater than real number of ports (" + count + ").");
      throw "Bad MIDI port number";
    }

    // No port selected yet, use heuristics
    if ( port_num === undefined )
    {
      for ( let i = 0; i < count; i++ )
      {
        const name = midiin.getPortName(i);
        if ( name.includes("Midi Through") )
          continue;
        if ( name.includes(repeater_name) )
        {
          is_repeater = true;
          port_num = i;
          break;
        }
        if ( port_num === undefined )
          port_num = i;
      }
    }

    // Open input port
    console.log("Opening input port number " + port_num);
    midiin.openPort(port_num);

    // Open output port
    this.midiout.openPort(port_num);

    // Prepare last_vals and setup callback
    midiin.ignoreTypes(false, false, false);

    // restore fader/slider values from RtMidi virtual port
    if ( is_repeater )
    {
      this.midiout.sendMessage([ 0xF0, 0x00, 0xF7 ]);
      this.midiout.closePort();
    }
  }

  setlog(b)
  {
    this.log = b;
  }

  onevent(v, func)
  {
    this.events[v] = func;
  }

  onbutton(v, func)
  {
    this.buttons[v] = func;
  }

  parse_events()
  {
    let midiin = this.midiin;
    if ( !midiin.isPortOpen() )
      return;
    while ( 42 )
    {
      let msg = midiin.getMessage();
      const msglen = msg.length;
      if ( msglen == 0 )
        break;
      if ( this.log )
        console.log(JSON.stringify(msg));
      if ( msglen == 3 )
      {
        if ( msg[0] == 176 )
        {
          let event_v = this.events[msg[1]];
          if ( event_v !== undefined )
            event_v(msg[2]);
          let button_v = this.buttons[msg[1]];
          if ( button_v !== undefined )
            button_v(msg[2] == 127);
        }
      }
    }
  }
}
