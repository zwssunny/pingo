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
    console.log("billWebSocket连接已打开");
};

// 监听WebSocket关闭事件
socket.onclose = function (e) {
    console.log("billWebSocket连接已关闭");
};

// 监听WebSocket消息事件
socket.onmessage = function (e) {
    var data = JSON.parse(e.data);
    if (data.action === "playoperate") {
        // console.log("收到新消息: ", data);
        buttonstate(data.playstate)
    }
};
//保存编辑窗体的原始值
var jsonTextInit='';
var selectItemID=0 ;
function buttonstate( playstate){
  //1-播放，2-暂停，0,4-已停止或者没有播放
  if (playstate==1)
  {
    $('button#UNPAUSE').disable();
    $('button#STOP').enable();
    $('button#PLAY').disable();
    $('button#PAUSE').enable();
    $('#bills-select').disable();
    $('#billItemsTable').disable();
    $('button#btBillEdit').disable();
    $('button#btBillCopy').disable();
    
  }
  else if(playstate==2){
    $('button#UNPAUSE').enable();
    $('button#STOP').enable();
    $('button#PLAY').disable();
    $('button#PAUSE').disable();
    $('#bills-select').disable();
    $('#billItemsTable').disable();
    $('button#btBillEdit').disable();
    $('button#btBillCopy').disable();
  }
  else
  {
    $('button#UNPAUSE').disable();
    $('button#STOP').disable();
    $('button#PLAY').enable();
    $('button#PAUSE').disable();
    $('#bills-select').enable();
    $('#billItemsTable').enable();
    $('button#btBillEdit').enable();
    $('button#btBillCopy').enable();
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

function getBillId()
{
    var e = $('#bills-select');  
    var selected_value = e.val();
    return selected_value
};
    //定义列定义
    columns=[
        { field: 'ENABLE', title: '状态', sortable: true
        ,formatter: function(val,row,index){
            if(val==1)
                return"启用";
            else
                return "禁用";
        }
        // ,editable: {
        //     title:"请选择是否启用：",
        //     type: "select",
        //     source: [{value:"1",text:"启用"},{value:"0",text: "禁用"}]
        //     }
        }, 
        { field: 'ORDERNO', title: '演示顺序', sortable: true
        // , editable: {
        //     title:"请输入序号：",
        //     type: "text",
        //     validate:function(v){
        //         v=v.trim();
        //         v=parseInt(v);
        //         if(isNaN(v)){return "请输入有效整数";}
        //     }
        //     } 
        },
        { field: 'TYPENAME', title: '节点分类', sortable: true },
        { field: 'TYPEID', title: '节点ID', visible: false },
        { field: 'NAME',title: '名称', sortable: true },
        { field: 'SLEEP',title: '等待-秒', sortable: true },
        { field: 'DESC', title: '演讲词', visible: false
        // , editable: {
        //     title: "请输入演讲词：",
        //     type: "textarea",
        //     validate: function (v) {
        //         v=v.trim();
        //         if(v.length>1000){return "长度不能大于1000";}
        //     }

        //     } 
        }, 
        { field: 'ID',title: '操作', align: 'center', valign: 'middle', formatter: actionFormatter }  
    ];
 //操作栏的格式化
 function actionFormatter(value, row, index) {
    var id = value;
    var result = "";
    if (row.ENABLE==1){
        result += "<a href='javascript:;' class='btn btn-info mb-2' style='margin:5px' onclick=\"SwitchEnableStatus("+id+","+row["ENABLE"]+",'禁用')\" title='禁用后不演示该节点'>";
        result += "<span class='fas fa-warning'></span>禁用</a>";
    }
    else{
        result += "<a href='javascript:;' class='btn btn-info mb-2' style='margin:5px' onclick=\"SwitchEnableStatus("+id+","+row["ENABLE"]+",'启用')\" title='启用该节目'>";
        result += "<span class='fas fa-success'></span>启用</a>";   
    }
    result += "<a href='javascript:;' class='btn btn-primary mb-2' style='margin:5px' onclick=\"EditViewById("+id+")\" title='编辑演讲内容'>";
    result += "<span class='fas fa-edit'></span>编辑</a>";
    if (row["TYPENAME"]=="FEATURES") {
        result += "<a href='javascript:;' class='btn btn-danger mb-2'  style='margin:5px' onclick=\"DeleteByIds("+id+")\" title='删除后不能恢复'>";
        result += "<span class='fas fa-trash'></span>删除</a>";
    }
    return result;
}
//
function SwitchEnableStatus(id,enablestatus,msg){
    if (enablestatus==1)
        enablestatus=0
    else
        enablestatus=1

    $.ajax({
        url: '/switchenable',
        type: "POST",
        data: {"id": id,"enable": enablestatus,'validate': getCookie('validation')},
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
            toastr.error('服务器异常', '获取节点数据失败');
        }
    });
    //刷新记录
    $('#billItemsTable').bootstrapTable('refresh');
}
//调用编辑窗体
function EditViewById(id){
    selectItemID=id;
    $.ajax({
        url: '/billitems',
        type: "GET",
        data: {"billid": getBillId(), "itemid":id,'validate': getCookie('validation')},
        success: function(res) {
            var data_json = JSON.parse(res);
            if (data_json.length>0)
            {
                // $("#itemid").val(data_json[0].ID);
                $("#itemname").val(data_json[0].NAME);
                $("#itemorderno").val(data_json[0].ORDERNO);
                $("#itemsleep").val(data_json[0].SLEEP);
                $("#itemdesc").text(data_json[0].DESC);
                //弹出修改模态框，非新增模态框
                $('#editModal').modal('show')
                // 暂存未修改时数据
                var dataformInit = $("#form_edit").serializeArray();
                jsonTextInit = JSON.stringify({ dataform: dataformInit });
            }
            else
            {
                toastr.error('找不到记录', '获取节点数据失败');
            }
        },
        error: function() {
            toastr.error('服务器异常', '获取节点数据失败');
        }
    });

}
//初始化列表
  function InitBillItemsTable() 
  { 
        $('#billItemsTable').bootstrapTable({
            url: '/billitems',
            method: 'get',
            columns: columns,
            resizable: true,
            pagination: true,
            sidePagination: 'client',
            striped: true,                      //是否显示行间隔色
            sortable: true,                     //是否启用排序
            sortOrder: 'asc',                   //排序方式
            clickToSelect: true,                //是否启用点击选中行
            pageNumber: 1,
            pageSize: 10,
            pageList: [10,20,30],
            search: true,
            showRefresh: true,
            showToggle: true,
            showColumns: true,
            queryParams: function (params){
                var param={
                    billid:  getBillId(),
                    validate:  getCookie('validation')
                 };
                 return param;
            }
        });
    };
//刷新剧本列表
function refreshBillsList() {
    //保存选中
    selected_value=getBillId()
    //暂时关闭事件触发
    $('#bills-select').attr("disabled", true)
    $('#bills-select').empty();
    $.ajax({
        url: '/bills',
        type: "GET",
        data: {'validate': getCookie('validation')},
        success: function(res) {
            var data_json = JSON.parse(res);
            if (data_json.length>0)
            {
                data_json.forEach(element => {
                    if (element.ISDEFAULT==1)
                        $('#bills-select').append('<option selected="selected" value ='+element.ID+' >'+element.NAME+'</option>')
                    else
                        $('#bills-select').append('<option value ='+element.ID+' >'+element.NAME+'</option>')      
                });
            }
            else
            {
                toastr.error('找不到记录', '获取剧本数据失败');
            }
        },
        error: function() {
            toastr.error('服务器异常', '获取剧本数据失败');
        }
    });  
   //恢复触发事件
    $('#bills-select').attr("disabled", false)

    if (selected_value)
        $('#bills-select').val(selected_value)
}

$(function() {
    
    $('button#STOP').on('click', function(e) {
        selected_value=getBillId();
        talkbill(4,selected_value,'停止');
        buttonstate(4);
    });
    $('button#PLAY').on('click', function(e) {
        selected_value=getBillId();
        talkbill(1,selected_value,'播放');
        buttonstate(1);
    });
    $('button#PAUSE').on('click', function(e) {
        selected_value=getBillId();
        talkbill(2,selected_value,'暂停');
        buttonstate(2);
    });
    $('button#UNPAUSE').on('click', function(e) {
        selected_value=getBillId();
        talkbill(3,selected_value,'继续');
        buttonstate(1);
    });

    //日期时间控件
    $("#billdatetime").datetimepicker({
        language: "zh-cn",
        format: "yyyy-mm-dd hh:ii",
        autoclose: true
      });
    //调整按钮初始化状态
    buttonstate(4);
    //初始化节目表
    InitBillItemsTable();
    //剧本变化时刷新节目单
    $('#bills-select').change(function () {
        $('#billItemsTable').bootstrapTable('refresh');
    });
    //关闭编辑窗体后清空
    $('#editModal').on('hidden.bs.modal', function () {
        // 清空表单
        $('#form_edit')[0].reset();
        // $("#itemid").val("");
        $("#itemname").val("");
        $("#itemorderno").val("0");
        $("#itemsleep").val("0");
        $("#itemdesc").text("");
    });
    //提交节点保存
    $("#but_submit_add").click(function () {
        // 判断是否修改
        var dataform = $("#form_edit").serializeArray();
        var jsonText = JSON.stringify({ dataform: dataform });
        if(jsonText == jsonTextInit) {
           $("#editModal").modal('hide');
           return;
        }
        var itemdata={"billid": getBillId(), 'validate': getCookie('validation'),"id": selectItemID,"orderno": $("#itemorderno").val(), 
        "sleep": $("#itemsleep").val(),"desc": encodeURIComponent($("#itemdesc").val())}
        $.ajax({
            url: '/billitems',
            type: "POST",
            data: itemdata,
            success: function(res) {
                var data = JSON.parse(res);
                msg='更新节点';
                if (data.code == 0) {
                    toastr.success(msg+'成功');
                } else {
                    toastr.error(data.message, msg+'失败');
                }
            },
            error: function() {
                toastr.error('服务器异常', '更新失败');
            }
        });
        //刷新记录
        $('#billItemsTable').bootstrapTable('refresh');
        $("#editModal").modal('hide');
    });
    //编辑剧本
    $('button#btBillEdit').on('click', function(e) {
        $.ajax({
            url: '/bills',
            type: "GET",
            data: {"billid": getBillId(), 'validate': getCookie('validation')},
            success: function(res) {
                var data_json = JSON.parse(res);
                if (data_json.length>0)
                {
                    // $("#itemid").val(data_json[0].ID);
                    $("#billname").val(data_json[0].NAME);
                    $("#billvoice").val(data_json[0].VOICE);
                    $("#billisdefault").val(data_json[0].ISDEFAULT);
                    $("#billdesc").text(data_json[0].DESC);
                    $("#billdatetime").val(data_json[0].DATETIME);
                    //弹出修改模态框，非新增模态框
                    $('#editBillModal').modal('show')
                    // 暂存未修改时数据
                    var dataformInit = $("#form_billedit").serializeArray();
                    jsonTextInit = JSON.stringify({ dataform: dataformInit });
                }
                else
                {
                    toastr.error('找不到记录', '获取剧本数据失败');
                }
            },
            error: function() {
                toastr.error('服务器异常', '获取剧本数据失败');
            }
        });

    });
        //关闭剧本编辑窗体后清空
        $('#editBillModal').on('hidden.bs.modal', function () {
            // 清空表单
            $('#form_billedit')[0].reset();
            $("#billname").val("");
            $("#billvoice").val("");
            $("#billisdefault").val("");
            $("#billdesc").text("");
            $("#billdatetime").val("");
        });
        //提交剧本保存
        $("#bill_submit_add").click(function () {
            // 判断是否修改
            var dataform = $("#form_billedit").serializeArray();
            var jsonText = JSON.stringify({ dataform: dataform });
            if(jsonText == jsonTextInit) {
               $("#editBillModal").modal('hide');
               return;
            }
            var billdata={'validate': getCookie('validation'),"id": getBillId(),"name": $("#billname").val(),
                    "isdefault": $("#billisdefault").val(),"voice": $("#billvoice").val(), 
                     "datetime": $("#billdatetime").val(), "desc": encodeURIComponent($("#billdesc").val())}
            $.ajax({
                url: '/bills',
                type: "POST",
                data: billdata,
                success: function(res) {
                    var data = JSON.parse(res);
                    msg='更新剧本';
                    if (data.code == 0) {
                        toastr.success(msg+'成功');
                    } else {
                        toastr.error(data.message, msg+'失败');
                    }
                },
                error: function() {
                    toastr.error('服务器异常', '更新失败');
                }
            });
            //刷新记录
            refreshBillsList();
            $("#editBillModal").modal('hide');
        });
    //克隆剧本
    $('button#btBillCopy').on('click', function(e) {
        selected_value=getBillId();
        alert("未实现")
    });
});
