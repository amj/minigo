var next_color = WGo.B;
var last_command = '';

var convert_gtp_coord =
    function(gtpcoord) {
  x = gtpcoord.charCodeAt(0) - 65;
  if (x >= 8) {
    x = x - 1
  }

  y = parseInt(gtpcoord.slice(1), 10);
  return {
    'x': x, 'y': y - 1
  }
}

var convert_wgo_coord =
    function(x, y) {
  if (x > 8) {
    x = x - 1
  }
  return String.fromCharCode(65 + x) + String(y + 1);
}

function handle_gtp_response(msg) {
  console.log(msg);
  if (msg[0] == '?') {
    return;
  }
  if (msg[0] == '=') {
    if (last_command == 'genmove') {
      rest = msg.slice(2);
      coords = convert_gtp_coord(rest)

      board.addObject({x: coords.x, y: coords.y, c: next_color});
      next_color = next_color == WGo.B ? WGo.W : WGo.B;
    }
    return;
  }
};

var handle_stderr_response = function(msg) {
  console.log(msg);
};

var board = new WGo.Board(document.getElementById('board'), {
  width: 600,
  size: 9,
});


function stdout_log(message) {
  if (message.length > 0) {
    $('#stdout').append($('<li>').text(message));
  }
}


$(document).ready(function() {
  // your code here
  var stdout_socket =
      io.connect('http://' + document.domain + ':' + location.port + '/stdout');
  var stdin_socket =
      io.connect('http://' + document.domain + ':' + location.port + '/stdin');
  var stderr_socket =
      io.connect('http://' + document.domain + ':' + location.port + '/stderr');


  stderr_socket.on('connect', function() {
    stderr_socket.emit('message', {data: 'stderr ready'});
  });

  stderr_socket.on('json', function(msg) {
    msg = JSON.parse(msg).stderr;
    if (msg.length == 0) {
      return;
    }
    $('#stderr').append($('<li>').text(msg));
    handle_stderr_response(msg)
  });

  stdout_socket.on('json', function(msg) {
    msg = JSON.parse(msg).stdout;
    if (msg.length == 0) {
      return;
    }

    stdout_log(msg);
    handle_gtp_response(msg);
  });


  stdin_socket.on('connect', function() {
    stdin_socket.emit('message', {data: 'stdin ready'});
  });


  $('form#stdin').submit(function(event) {
    data = $('#stdin_data').val();
    console.log(data);

    stdin_socket.emit('my event', {data: data});
    stdout_log(data)
    last_command = data.split(' ')[0];
    return false;
  });


  board.addEventListener('click', function(x, y) {
    board.addObject({x: x, y: y, c: next_color});
    color = next_color == WGo.B ? 'b ' : 'w ';
    play_cmd = 'play ' + color + convert_wgo_coord(x, y);
    stdout_log(play_cmd);
    stdin_socket.emit('my event', {
      data: play_cmd,
    });
    next_color = (next_color == WGo.B) ? WGo.W : WGo.B;
  });
});
