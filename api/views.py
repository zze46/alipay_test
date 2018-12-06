from django.shortcuts import render, redirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from utils.pay import AliPay
import time
from django.conf import settings


def aliPay():
    obj = AliPay(
        appid=settings.APPID,
        app_notify_url=settings.NOTIFY_URL,  # 如果支付成功，支付宝会向这个地址发送POST请求（校验是否支付已经完成）
        return_url=settings.RETURN_URL,  # 如果支付成功，重定向回到你的网站的地址。
        alipay_public_key_path=settings.PUB_KEY_PATH,  # 支付宝公钥
        app_private_key_path=settings.PRI_KEY_PATH,  # 应用私钥
        debug=True,  # 默认False,
    )
    return obj


def index(request):
    if request.method == 'GET':
        return render(request, 'index.html')

    alipay = aliPay()

    # 对购买的数据进行加密
    money = float(request.POST.get('price'))
    out_trade_no = "x2" + str(time.time())
    # 1. 在数据库创建一条数据：状态（待支付）

    query_params = alipay.direct_pay(
        subject="充气式娃娃",  # 商品简单描述
        out_trade_no=out_trade_no,  # 商户订单号
        total_amount=money,  # 交易金额(单位: 元 保留俩位小数)
    )

    pay_url = "https://openapi.alipaydev.com/gateway.do?{}".format(query_params)
    return redirect(pay_url)


def pay_result(request):
    """
    支付完成后，跳转回的地址
    :param request:
    :return:
    """
    params = request.GET.dict()
    sign = params.pop('sign', None)

    alipay = aliPay()
    # 校验支付是否成功
    status = alipay.verify(params, sign)

    if status:
        return HttpResponse('成功')
    return HttpResponse('失败')


@csrf_exempt
def update_order(request):
    """
    支付成功后，支付宝向该地址发送的POST请求（用于修改订单状态，要求在公网环境下）
    """
    if request.method == 'POST':
        from urllib.parse import parse_qs

        body_str = request.body.decode('utf-8')
        post_data = parse_qs(body_str)

        post_dict = {}
        for k, v in post_data.items():
            post_dict[k] = v[0]

        alipay = aliPay()

        sign = post_dict.pop('sign', None)
        status = alipay.verify(post_dict, sign)
        if status:
            # 1. 获取订单号
            out_trade_no = post_dict.get('out_trade_no')
            print(out_trade_no)
            # 2. 根据订单号将数据库中的数据进行更新
            return HttpResponse('success')
        else:
            return HttpResponse('fail')
    return HttpResponse('')
