from typing import Any
from mcp.server.fastmcp import FastMCP

# 初始化 MCP 服务器
mcp = FastMCP("toolsServer")


@mcp.tool()
async def open_page(pageName: str) -> Any:
    """打开指定页面,并返回页面内容介绍

    Args:
        pageName (str): 页面名称

    Returns:
        Any: 返回该页面的内容介绍
    """    
    return pageName



@mcp.tool()
async def open_other_system(systemName: str) -> Any:
    """打开第三方系统，并介绍系统功能

    Args:
        systemName (str): 第三方系统名称

    Returns:
        Any: 第三方系统功能介绍
    """    
    # 
    return systemName



@mcp.tool()
async def Demo_platform() -> Any:
    """演示或者介绍平台功能

    Returns:
        Any: 成功返回
    """    
    return {"result": "success"}


if __name__ == "__main__":
    # 以标准 I/O 方式运行 MCP 服务器
    mcp.run(transport="stdio")
