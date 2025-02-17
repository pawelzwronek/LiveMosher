import * as rtmidi from 'rtmidi';
import * as zmq from "zmq";

export class MIDIInput {
    keys = [];

    constructor() {
        this.midiin = new rtmidi.In(rtmidi.UNSPECIFIED, 'RtMidi Input Client', 1024);
        this.midiout = new rtmidi.Out();

        // Fallback to ZMQ if no MIDI ports are available
        this.zmq = undefined;
        this.zpull = undefined;

        this.events = {};
        this.buttons = {};

        this.log = false;

        const octaves = [0, 7];
        const notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
        for (let octave = octaves[0]; octave <= octaves[1]; octave++) {
            for (let key = 0; key < 12; key++) {
                this.keys.push(notes[key] + octave);
            }
        }

    }

    setup(arg) {
        let port_name;
        let port_num;
        const midiin = this.midiin;
        const repeater_name = 'RtMidi Repeater';
        let is_repeater = false;

        // Check arguments
        if (arg !== undefined) {
            if (typeof arg === 'string') port_name = arg;
            else port_num = arg;
        }

        // Check if any MIDI ports are available
        const count = midiin.getPortCount();

        console.log('RtMidi: ' + count + ' port' + (count > 1 ? 's' : '') + ' found');

        // Print names and select port number
        for (let i = 0; i < count; i++) {
            const name = midiin.getPortName(i);
            if (name == port_name) port_num = i;
            console.log(i + '. ' + name);
        }

        // Sanity check for port name
        if (port_name !== undefined && port_num === undefined) {
            console.log('Selected port name (' + port_name + ') is not available.');
            throw 'Bad MIDI port name';
        }

        // Sanity check for port number
        if (port_num >= count) {
            printf('Selected port number (' + port_num + ') greater than real number of ports (' + count + ').');
            throw 'Bad MIDI port number';
        }

        // No port selected yet, use heuristics
        if (port_num === undefined) {
            for (let i = 0; i < count; i++) {
                const name = midiin.getPortName(i);
                if (name.includes('Midi Through')) continue;
                if (name.includes(repeater_name)) {
                    is_repeater = true;
                    port_num = i;
                    break;
                }
                if (port_num === undefined) port_num = i;
            }
        }

        if (port_num !== undefined) {
            // Open input port
            console.log('Opening input port number ' + port_num);
            midiin.openPort(port_num);

            // Open output port
            this.midiout.openPort(port_num);

            // Prepare last_vals and setup callback
            midiin.ignoreTypes(false, false, false);

            // restore fader/slider values from RtMidi virtual port
            if (is_repeater) {
                this.midiout.sendMessage([0xf0, 0x00, 0xf7]);
                this.midiout.closePort();
            }
        }
        else
        {
            this.zmq = new zmq.Context();
            this.zpull = this.zmq.socket(zmq.PULL);
            const ret = this.zpull.bind('tcp://localhost:0');
            if (ret == -1) {
                console.log('ZMQ bind failed: ' + ret);
                this.zmq = undefined;
                this.zpull = undefined;
                throw 'No MIDI ports. ZMQ bind failed';
            }
            const bound_url = this.zpull.getsockopt(zmq.LAST_ENDPOINT);
            // DON'T CHANGE THE FOLLOWING LINE, IT'S USED FOR DETECTING THE ZMQ URL IN MAIN APP
            console.log('No MIDI ports. Falling back to ZMQ midi eumulation on: ' + bound_url);
        }
    }

    setlog(b) {
        this.log = b;
    }

    midi_note_to_key(note = 0) {
        if (note < 10) return 'Fader ' + note;

        const C0 = 12;
        if (note >= C0 && note < C0 + this.keys.length)
            return this.keys[note - C0];
        else
            return 'C?';
    }

    _pad_end(str, len, pad) {
        return str + pad.repeat(Math.max(0, len - str.length));
    }

    onevent(v, func) {
        this.events[v] = func;
        console.log('Registered event for note: ' + this._pad_end(this.midi_note_to_key(v), 3, ' ') + ' (' + v + ')');
    }

    onbutton(v, func) {
        this.buttons[v] = func;
        console.log('Registered button for note: ' + this._pad_end(this.midi_note_to_key(v), 3, ' ') + ' (' + v + ')');
    }

    parse_events() {
        let midiin = this.midiin;
        if (!midiin.isPortOpen() && !this.zpull)
            return;

        while (true) {
            let msg = [];

            if (midiin.isPortOpen()) {
                msg = midiin.getMessage();
            } else if (this.zpull) {
                const msg_str = this.zpull.recv_str(zmq.DONTWAIT);
                if (msg_str === undefined) break;
                msg = JSON.parse(msg_str);
            }

            if (msg.length === 0) break;
            if (this.log) console.log(JSON.stringify(msg));

            if (msg.length === 3) {
                let status = msg[0];
                let channel = status & 0x0f;
                let type = status & 0xf0;
                let note = msg[1];
                let velocity = msg[2];

                // Call the event handler if one is registered for this note
                let eventHandler = this.events[note];
                if (eventHandler) {
                    eventHandler({
                        status: status,
                        channel: channel,
                        note: note,
                        velocity: velocity,
                        type: type,
                    });
                }

                // Call the button handler if one is registered for this note
                let buttonHandler = this.buttons[note];
                if (buttonHandler) {
                    let pressed = type === 0x90 && velocity > 0; // Note On with velocity > 0
                    let released = type === 0x80 || (type === 0x90 && velocity === 0); // Note Off, or Note On with velocity 0
                    if (pressed || released) {
                        buttonHandler(pressed); // true if pressed, false if released
                    }
                }
            }
        }
    }
}
