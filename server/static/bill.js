function talkbill(operate, billid, billitemid, msg) {
    $.ajax({
        url: '/operate',
        type: "POST",
        data: { "type": operate, "billid": billid, "billitemid": billitemid, 'validate': getCookie('validation') },
        success: function (res) {
            var data = JSON.parse(res);
            if (!msg) msg = '';
            if (data.code == 0) {
                toastr.success(msg + '成功');
            } else {
                toastr.error(data.message, msg + '失败');
            }
        },
        error: function () {
            toastr.error('服务器异常', msg + '失败');
        }
    });
}
//获取播放状态
function getbillplaystatus() {
    $.ajax({
        url: '/operate',
        type: "POST",
        data: { "type": 5, 'validate': getCookie('validation') },
        success: function (res) {
            var data = JSON.parse(res);
            console.log("收到播放状态: ", data);
            msg = '获取播放状态';
            if (data.code == 0) {
                if (data.curbillid) {
                    $('#bills-select').val(data.curbillid);
                    $('#billItemsTable').bootstrapTable('refresh');
                }
                if (data.curbillitemid) {
                    $('#billItemsTable').bootstrapTable('checkBy', { field: 'ID', values: [data.curbillitemid] });
                }
                buttonstate(data.playstatus)
                toastr.success(msg + '成功');
            } else {
                toastr.error(data.message, msg + '失败');
            }
        },
        error: function () {
            toastr.error('服务器异常', msg + '失败');
        }
    });
}
// 创建WebSocket连接
var socket = new WebSocket("wss://" + location.host + "/websocket");

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
        console.log("收到新消息: ", data);
        if (data.billid) {
            $('#bills-select').val(data.billid)
        }
        if (data.billitemid) {
            $('#billItemsTable').bootstrapTable('checkBy', { field: 'ID', values: [data.billitemid] });
        }
        buttonstate(data.playstatus)
    }
};
//保存编辑窗体的原始值
var jsonTextInit = '';
var selectItemID = 0;
function buttonstate(playstatus) {
    //1-播放，2-暂停，0,4-已停止或者没有播放
    if (playstatus == 1) {
        $('button#UNPAUSE').disable();
        $('button#showstopModal').enable();
        $('button#PLAY').disable();
        $('button#PAUSE').enable();
        $('#bills-select').disable();
        $('#billItemsTable').disable();
        $('button#btBillEdit').disable();
        $('button#btBillCopy').disable();

    }
    else if (playstatus == 2) {
        $('button#UNPAUSE').enable();
        $('button#showstopModal').enable();
        $('button#PLAY').disable();
        $('button#PAUSE').disable();
        $('#bills-select').disable();
        $('#billItemsTable').disable();
        $('button#btBillEdit').disable();
        $('button#btBillCopy').disable();
    }
    else {
        $('button#UNPAUSE').disable();
        $('button#showstopModal').disable();
        $('button#PLAY').enable();
        $('button#PAUSE').disable();
        $('#bills-select').enable();
        $('#billItemsTable').enable();
        $('button#btBillEdit').enable();
        $('button#btBillCopy').enable();
    }

}

jQuery.fn.disable = function () {
    this.enable(false);
    return this;
};

jQuery.fn.enable = function (opt_enable) {
    if (arguments.length && !opt_enable) {
        this.attr("disabled", "disabled");
    } else {
        this.removeAttr("disabled");
    }
    return this;
};

function getBillId() {
    var e = $('#bills-select');
    var selected_value = e.val();
    return selected_value
};
//定义列定义
columns = [
    { radio: true },
    {
        field: 'ENABLE', title: '状态', sortable: true, width: '50', align: 'center'
        , formatter: function (val, row, index) {
            if (val == 1)
                return "启用";
            else
                return "禁用";
        }
    },
    { field: 'ORDERNO', title: '顺序', sortable: true, width: '50', align: 'center' },
    { field: 'TYPENAME', title: '节点分类', sortable: true, width: '50', align: 'center' },
    { field: 'TYPEID', title: '节点ID', visible: false, switchable: false },
    { field: 'NAME', title: '名称', sortable: true, width: '250', align: 'left' },
    { field: 'SLEEP', title: '等待(秒)', sortable: true, width: '50', align: 'center' },
    { field: 'DESC', title: '演讲词', visible: false },
    { field: 'ID', title: '操作', width: '350', align: 'center', valign: 'middle', formatter: actionFormatter }
];
//操作栏的格式化
function actionFormatter(value, row, index) {
    var id = value;
    var result = "";
    if (row.ENABLE == 1) {
        result += "<a href='javascript:;' class='btn btn-info mb-2' style='margin:5px' onclick=\"SwitchEnableStatus(" + id + "," + row["ENABLE"] + ",'禁用')\" title='禁用后不演示该节点'>";
        result += "<span class='fas fa-warning'></span>禁用</a>";
    }
    else {
        result += "<a href='javascript:;' class='btn btn-info mb-2' style='margin:5px' onclick=\"SwitchEnableStatus(" + id + "," + row["ENABLE"] + ",'启用')\" title='启用该节目'>";
        result += "<span class='fas fa-success'></span>启用</a>";
    }
    result += "<a href='javascript:;' class='btn btn-primary mb-2' style='margin:5px' onclick=\"EditViewById(" + id + ")\" title='编辑演讲内容'>";
    result += "<span class='fas fa-edit'></span>编辑</a>";
    // if (row["TYPENAME"] == "FEATURES") {
    //     result += "<a href='javascript:;' class='btn btn-danger mb-2' style='margin:5px' onclick=\"DeleteById(" + id + ")\" title='删除后不能恢复'>";
    //     result += "<span class='fas fa-trash'></span>删除</a>";
    // }
    result += "<a href='javascript:;' class='btn btn-success mb-2' style='margin:5px' onclick=\"PlayById(" + id + ")\" title='播放该节点演讲内容'>";
    result += "<span class='fas fa-play'></span>播放</a>";
    return result;
}
//
function SwitchEnableStatus(id, enablestatus, msg) {
    if (enablestatus == 1)
        enablestatus = 0
    else
        enablestatus = 1

    $.ajax({
        url: '/switchenable',
        type: "POST",
        data: { "id": id, "enable": enablestatus, 'validate': getCookie('validation') },
        success: function (res) {
            var data = JSON.parse(res);
            if (!msg) msg = '';
            if (data.code == 0) {
                //更新记录
                $('#billItemsTable').bootstrapTable('updateByUniqueId', {
                    id: id, row: {
                        "ENABLE": enablestatus
                    }
                });
                toastr.success(msg + '成功');
            } else {
                toastr.error(data.message, msg + '失败');
            }
        },
        error: function () {
            toastr.error('服务器异常', '获取节点数据失败');
        }
    });
    //刷新记录
    // $('#billItemsTable').bootstrapTable('refresh');
}
//演示节点
function PlayById(id) {
    selectItemID = id;
    selected_value = getBillId();
    talkbill(1, selected_value, selectItemID, '播放')
}
//删除节点
function DeleteById(id) {
    selectItemID = id;
    //弹出删除模态框
    $('#deleteModal').modal('show')
}
//调用编辑窗体
function EditViewById(id) {
    selectItemID = id;
    $.ajax({
        url: '/billitems',
        type: "GET",
        data: { "billid": getBillId(), "itemid": id, 'validate': getCookie('validation') },
        success: function (res) {
            var data_json = JSON.parse(res);
            if (data_json.length > 0) {
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
            else {
                toastr.error('找不到记录', '获取节点数据失败');
            }
        },
        error: function () {
            toastr.error('服务器异常', '获取节点数据失败');
        }
    });

}
//初始化列表
function InitBillItemsTable() {
    $('#billItemsTable').bootstrapTable({
        url: '/billitems',
        method: 'get',
        columns: columns,
        uniqueId: 'ID',
        resizable: true,
        pagination: true,
        sidePagination: 'client',
        clickToSelect: true,
        maintainSelected: true,
        striped: true,                      //是否显示行间隔色
        sortable: true,                     //是否启用排序
        sortOrder: 'asc',                   //排序方式
        singleSelect: true,             //单选
        pageNumber: 1,
        pageSize: 10,
        pageList: [10, 20, 30],
        search: true,
        showRefresh: true,
        showToggle: true,
        showColumns: true,
        queryParams: function (params) {
            var param = {
                billid: getBillId(),
                validate: getCookie('validation')
            };
            return param;
        }
    });
};
//刷新演讲方案列表
function refreshBillsList(selectedvalue) {
    try {
        //暂时关闭事件触发
        $('#bills-select').attr("disabled", true)
        $('#bills-select').empty();
        $.ajax({
            url: '/bills',
            type: "GET",
            data: { 'validate': getCookie('validation') },
            success: function (res) {
                var data_json = JSON.parse(res);
                if (data_json.length > 0) {
                    data_json.forEach(element => {
                        if (element.ID == selectedvalue)
                            $('#bills-select').append('<option selected="selected" value =' + element.ID + ' >' + element.NAME + '</option>')
                        else
                            $('#bills-select').append('<option value =' + element.ID + ' >' + element.NAME + '</option>')
                    });
                }
                else {
                    toastr.error('找不到记录', '获取数据失败');
                }
            },
            error: function () {
                toastr.error('服务器异常', '获取数据失败');
            }
        });
    }
    finally {
        //恢复触发事件
        $('#bills-select').attr("disabled", false)
    }

}

$(function () {

    $('button#STOP').on('click', function (e) {
        selected_value = getBillId();
        talkbill(4, selected_value, 0, '停止');
        buttonstate(4);
        $("#stopModal").modal('hide');
    });
    $('button#PLAY').on('click', function (e) {
        selected_value = getBillId();
        talkbill(1, selected_value, 0, '播放');
        buttonstate(1);
    });
    $('button#PAUSE').on('click', function (e) {
        selected_value = getBillId();
        talkbill(2, selected_value, 0, '暂停');
        buttonstate(2);
    });
    $('button#UNPAUSE').on('click', function (e) {
        selected_value = getBillId();
        talkbill(3, selected_value, 0, '继续');
        buttonstate(1);
    });

    //调整按钮初始化状态
    buttonstate(4);
    //初始化节目表
    InitBillItemsTable();
    //方案变化时刷新节目单
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
        if (jsonText == jsonTextInit) {
            $("#editModal").modal('hide');
            return;
        }
        var itemdata = {
            "billid": getBillId(), 'validate': getCookie('validation'), "id": selectItemID, "orderno": $("#itemorderno").val(),
            "sleep": $("#itemsleep").val(), "desc": encodeURIComponent($("#itemdesc").val())
        }
        $.ajax({
            url: '/billitems',
            type: "POST",
            data: itemdata,
            success: function (res) {
                var data = JSON.parse(res);
                msg = '更新节点';
                if (data.code == 0) {
                    toastr.success(msg + '成功');
                    //更新记录
                    $('#billItemsTable').bootstrapTable('updateByUniqueId', {
                        id: selectItemID, row: {
                            "ORDERNO": $("#itemorderno").val(),
                            "SLEEP": $("#itemsleep").val(), "DESC": $("#itemdesc").val(),
                        }
                    });
                } else {
                    toastr.error(data.message, msg + '失败');
                }
            },
            error: function () {
                toastr.error('服务器异常', '更新失败');
            }
        });
        //刷新记录
        // $('#billItemsTable').bootstrapTable('refresh');
        $("#editModal").modal('hide');
    });
    //编辑方案
    $('button#btBillEdit').on('click', function (e) {
        $.ajax({
            url: '/bills',
            type: "GET",
            data: { "billid": getBillId(), 'validate': getCookie('validation') },
            success: function (res) {
                var data_json = JSON.parse(res);
                if (data_json.length > 0) {
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
                else {
                    toastr.error('找不到记录', '获取数据失败');
                }
            },
            error: function () {
                toastr.error('服务器异常', '获取数据失败');
            }
        });

    });
    //关闭方案编辑窗体后清空
    $('#editBillModal').on('hidden.bs.modal', function () {
        // 清空表单
        $('#form_billedit')[0].reset();
        $("#billname").val("");
        $("#billvoice").val("");
        $("#billisdefault").val("");
        $("#billdesc").text("");
        $("#billdatetime").val(getCurrentTime());
    });
    //提交方案保存
    $("#bill_submit_add").click(function () {
        selected_value = getBillId();
        // 判断是否修改
        var dataform = $("#form_billedit").serializeArray();
        var jsonText = JSON.stringify({ dataform: dataform });
        if (jsonText == jsonTextInit) {
            $("#editBillModal").modal('hide');
            return;
        }
        var billdata = {
            'validate': getCookie('validation'), "id": selected_value, "name": $("#billname").val(),
            "isdefault": $("#billisdefault").val(), "voice": $("#billvoice").val(),
            "datetime": $("#billdatetime").val(), "desc": encodeURIComponent($("#billdesc").val())
        }
        $.ajax({
            url: '/bills',
            type: "POST",
            data: billdata,
            success: function (res) {
                var data = JSON.parse(res);
                msg = '更新演讲方案';
                if (data.code == 0) {
                    toastr.success(msg + '成功');
                } else {
                    toastr.error(data.message, msg + '失败');
                }
            },
            error: function () {
                toastr.error('服务器异常', '更新失败');
            }
        });
        //刷新记录
        refreshBillsList(selected_value);
        if (selected_value)
            $('#bills-select').val(selected_value)

        $("#editBillModal").modal('hide');
    });
    //克隆演讲方案
    $('button#CLONE').on('click', function (e) {
        var billdata = { 'validate': getCookie('validation'), "id": selected_value }
        $.ajax({
            url: '/bills',
            type: "PUT",
            data: billdata,
            success: function (res) {
                var data = JSON.parse(res);
                msg = '克隆演讲方案';
                if (data.code == 0) {
                    selected_value = data.newbillid;
                    //刷新记录
                    refreshBillsList(selected_value);
                    if (selected_value)
                        $('#bills-select').val(selected_value)
                    toastr.success(msg + '成功');
                } else {
                    toastr.error(data.message, msg + '失败');
                }
            },
            error: function () {
                toastr.error('服务器异常', '克隆失败');
            }
        });
        $("#cloneModal").modal('hide');
    });
    //新增演讲方案
    $('button#NEWBILL').on('click', function (e) {
        var billdata = { 'validate': getCookie('validation') }
        $.ajax({
            url: '/bills',
            type: "PATCH",
            data: billdata,
            success: function (res) {
                var data = JSON.parse(res);
                msg = '新增演讲方案';
                if (data.code == 0) {
                    selected_value = data.newbillid;
                    //刷新记录
                    refreshBillsList(selected_value);
                    if (selected_value)
                        $('#bills-select').val(selected_value)
                    toastr.success(msg + '成功');
                } else {
                    toastr.error(data.message, msg + '失败');
                }
            },
            error: function () {
                toastr.error('服务器异常', '接口调用失败');
            }
        });
        $("#newBillModal").modal('hide');
    });
    //删除节点记录
    $('button#DELETE').on('click', function (e) {
        var itemsdata = { 'validate': getCookie('validation'), "id": selectItemID }
        $.ajax({
            url: '/billitems',
            type: "DELETE",
            data: itemsdata,
            success: function (res) {
                var data = JSON.parse(res);
                msg = '删除节点';
                if (data.code == 0) {
                    //删除本地记录
                    $('#billItemsTable').bootstrapTable('removeByUniqueId', selectItemID);
                    toastr.success(msg + '成功');
                } else {
                    toastr.error(data.message, msg + '失败');
                }
            },
            error: function () {
                toastr.error('服务器异常', '操作失败');
            }
        });
        //关闭窗体
        $("#deleteModal").modal('hide');
    });
    //声音测试TESTVOICE
    $('button#TESTVOICE').on('click', function (e) {
        voice = $('#billvoice').val()
        var voicedata = { 'validate': getCookie('validation'), "voice": voice }
        $.ajax({
            url: '/voice',
            type: "POST",
            data: voicedata,
            success: function (res) {
                var data = JSON.parse(res);
                msg = '测试声音';
                if (data.code == 0) {
                    toastr.success(msg + '成功');
                } else {
                    toastr.error(data.message, msg + '失败');
                }
            },
            error: function () {
                toastr.error('服务器异常', '测试失败');
            }
        });
    });
    //获取服务器播放状态
    getbillplaystatus();
});
