function talkbill(operate,billid,msg) {
    $.ajax({
        url: '/operate',
        type: "POST",
        data: {"type": operate, "billid": billid, 'validate': getCookie('validation')},
        success: function(res) {
            var data = JSON.parse(res);
            if (!msg) msg='';
            if (data.code == 0) {
                toastr.success(msg+'成功');
            } else {
                toastr.error(data.message, msg+'失败');
            }
        },
        error: function() {
            toastr.error('服务器异常', msg+'失败');
        }
    });
}
// 创建WebSocket连接
var socket = new WebSocket("ws://" + location.host + "/websocket");

// 监听WebSocket打开事件
socket.onopen = function (e) {
    console.log("WebSocket连接已打开");
};

// 监听WebSocket关闭事件
socket.onclose = function (e) {
    console.log("WebSocket连接已关闭");
};

// 监听WebSocket消息事件
socket.onmessage = function (e) {
    var data = JSON.parse(e.data);
    if (data.action === "playoperate") {
        // console.log("收到新消息: ", data);
        buttonstate(data.playstate)
    }
};

function buttonstate( playstate){
  //1-播放，2-暂停，0,4-已停止或者没有播放
  if (playstate==1)
  {
    $('button#UNPAUSE').disable();
    $('button#STOP').enable();
    $('button#PLAY').disable();
    $('button#PAUSE').enable();
    $('#bills-select').disable();
  }
  else if(playstate==2){
    $('button#UNPAUSE').enable();
    $('button#STOP').enable();
    $('button#PLAY').disable();
    $('button#PAUSE').disable();
    $('#bills-select').disable();
  }
  else
  {
    $('button#UNPAUSE').disable();
    $('button#STOP').disable();
    $('button#PLAY').enable();
    $('button#PAUSE').disable();
    $('#bills-select').enable();
  }
  
}

jQuery.fn.disable = function() {
    this.enable(false);
    return this;
};

jQuery.fn.enable = function(opt_enable) {
    if (arguments.length && !opt_enable) {
        this.attr("disabled", "disabled");
    } else {
        this.removeAttr("disabled");
    }
    return this;
};

$(function() {
    $.ajax({
        url: '/bill',
        type: "GET",
        data: {'validate': getCookie('validation')},
        success: function(res) {
            var data = JSON.parse(res);            
            if (data.code == 0) {
                let bills = data.bills;
                selectitems=''
                bills.forEach( function(item){
                  if(item.ISDEFAULT==1)
                    selectitems+='<option  selected="selected" value='+item.ID+'>'+item.NAME+'</option> '
                  else
                    selectitems+='<option value='+item.ID+'>'+item.NAME+'</option> ' 
                } ) 
                  
                    $('#bills-placeholder').append(`
    <div class="input-group" id="container">
    <select class="form-control" id="bills-select" name="bills-select">`+selectitems +`</select>
    </div>

`);
     
                $('button#STOP').on('click', function(e) {
                    var e = $('#bills-select');  
                    var selected_value = e.val();
                    talkbill(4,selected_value,'停止');
                    buttonstate(4)
                });
                $('button#PLAY').on('click', function(e) {
                    var e = $('#bills-select');  
                    var selected_value = e.val();
                    talkbill(1,selected_value,'播放');
                    buttonstate(1)
                });
                $('button#PAUSE').on('click', function(e) {
                    var e = $('#bills-select');  
                    var selected_value = e.val();
                    talkbill(2,selected_value,'暂停');
                    buttonstate(2)
                });
                $('button#UNPAUSE').on('click', function(e) {
                    var e = $('#bills-select');  
                    var selected_value = e.val();
                    talkbill(3,selected_value,'继续');
                    buttonstate(1)
                });
            } else {
                toastr.error(data.message, '指令发送失败');
            }
        },
        error: function() {
            toastr.error('服务器异常', '指令发送失败');
        }
    });   
    //调整按钮初始化状态
    buttonstate(4);
});

