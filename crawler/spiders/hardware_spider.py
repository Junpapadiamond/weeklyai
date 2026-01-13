"""
AI 硬件产品爬虫
爬取 CES、各大科技媒体报道的 AI 硬件产品
"""

import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .base_spider import BaseSpider


class AIHardwareSpider(BaseSpider):
    """AI 硬件产品爬虫"""
    
    # 硬件产品数据源
    SOURCES = {
        'ces': 'https://www.ces.tech',
        'theverge': 'https://www.theverge.com',
        'techcrunch': 'https://techcrunch.com',
    }
    
    def crawl(self) -> List[Dict[str, Any]]:
        """爬取 AI 硬件产品"""
        products = []
        
        print("  [AI Hardware] 获取硬件产品信息...")
        
        # 策略1: 精选AI硬件数据库（基于真实产品）
        curated_products = self._get_curated_hardware()
        products.extend(curated_products)
        print(f"    ✓ 精选硬件库: {len(curated_products)} 个产品")
        
        # 策略2: 爬取科技媒体（可选）
        # media_products = self._crawl_tech_media()
        # products.extend(media_products)
        
        print(f"  [AI Hardware] 共获取 {len(products)} 个硬件产品")
        return products
    
    def _get_curated_hardware(self) -> List[Dict[str, Any]]:
        """精选的AI硬件产品数据库"""
        hardware_products = [
            {
                'name': 'NVIDIA H100',
                'description': 'NVIDIA 最强大的AI加速器，采用Hopper架构，专为大规模AI训练和推理设计，支持Transformer Engine和FP8精度。',
                'website': 'https://www.nvidia.com/en-us/data-center/h100/',
                'logo_url': 'https://www.nvidia.com/content/dam/en-zz/Solutions/about-nvidia/logo-and-brand/01-nvidia-logo-horiz-500x200-2c50-d@2x.png',
                'categories': ['hardware'],
                'price': '$30,000+',
                'release_year': 2023,
                'rating': 4.9,
                'trending_score': 95,
            },
            {
                'name': 'Apple M4 Pro',
                'description': 'Apple 最新一代芯片，集成强大的神经引擎，支持本地AI推理，16核CPU和40核GPU，专为AI工作负载优化。',
                'website': 'https://www.apple.com/m4-pro/',
                'logo_url': 'https://www.apple.com/ac/globalnav/7/en_US/images/be15095f-5a20-57d0-ad14-cf4c638e223a/globalnav_apple_image__b5er5ngrzxqq_large.svg',
                'categories': ['hardware'],
                'price': '$2,000+',
                'release_year': 2024,
                'rating': 4.8,
                'trending_score': 92,
            },
            {
                'name': 'Rabbit R1',
                'description': 'AI原生便携设备，搭载大型行动模型(LAM)，通过自然语言控制各种应用和服务，橙色方形设计极具辨识度。',
                'website': 'https://www.rabbit.tech/rabbit-r1',
                'logo_url': 'https://www.rabbit.tech/favicon.ico',
                'categories': ['hardware', 'voice'],
                'price': '$199',
                'release_year': 2024,
                'rating': 3.5,
                'trending_score': 65,  # Lowered - mixed reviews, not as hyped
            },
            {
                'name': 'Humane AI Pin',
                'description': '可穿戴AI设备，投影显示界面，支持语音交互、拍照翻译、实时信息查询，无需手机即可使用。',
                'website': 'https://humane.com',
                'logo_url': 'https://humane.com/favicon.ico',
                'categories': ['hardware', 'voice'],
                'price': '$699',
                'release_year': 2024,
                'rating': 2.8,
                'trending_score': 55,  # Lowered - poor reviews, company struggles
            },
            {
                'name': 'Meta Ray-Ban Smart Glasses',
                'description': 'Meta与Ray-Ban合作的AI智能眼镜，内置摄像头和AI助手，支持拍照、视频、语音助手和实时翻译。',
                'website': 'https://www.meta.com/smart-glasses/',
                'logo_url': 'https://static.xx.fbcdn.net/rsrc.php/yb/r/hLRJ1GG_y0J.ico',
                'categories': ['hardware', 'voice', 'image'],
                'price': '$299',
                'release_year': 2023,
                'rating': 4.3,
                'trending_score': 85,
            },
            {
                'name': 'Google Tensor G4',
                'description': 'Google自研的Tensor芯片，为Pixel手机提供强大的AI能力，支持Magic Eraser、实时翻译、增强语音识别等功能。',
                'website': 'https://store.google.com/product/pixel_9_pro',
                'logo_url': 'https://www.google.com/favicon.ico',
                'categories': ['hardware'],
                'price': '$999+',
                'release_year': 2024,
                'rating': 4.6,
                'trending_score': 87,
            },
            {
                'name': 'Cerebras CS-3',
                'description': '全球最大的AI芯片，拥有4万亿晶体管，专为大规模AI训练设计，单芯片即可训练GPT级模型。',
                'website': 'https://www.cerebras.net/product-chip/',
                'logo_url': 'https://www.cerebras.net/favicon.ico',
                'categories': ['hardware'],
                'price': 'Enterprise',
                'release_year': 2024,
                'rating': 4.8,
                'trending_score': 90,
            },
            {
                'name': 'AMD MI300X',
                'description': 'AMD 最新AI加速器，采用3D chiplet设计，192GB HBM3内存，专为大语言模型推理优化。',
                'website': 'https://www.amd.com/en/products/accelerators/instinct/mi300/mi300x.html',
                'logo_url': 'https://www.amd.com/etc.clientlibs/settings/wcm/designs/amd/images/favicons/favicon-32.png',
                'categories': ['hardware'],
                'price': '$15,000+',
                'release_year': 2023,
                'rating': 4.7,
                'trending_score': 86,
            },
            {
                'name': 'Rewind Pendant',
                'description': 'AI可穿戴录音设备，全天候记录对话和声音，自动生成会议记录和总结，注重隐私保护。',
                'website': 'https://www.rewind.ai/pendant',
                'logo_url': 'https://www.rewind.ai/favicon.ico',
                'categories': ['hardware', 'voice'],
                'price': '$59/month',
                'release_year': 2024,
                'rating': 4.1,
                'trending_score': 78,
            },
            {
                'name': 'Frame AI Glasses',
                'description': 'Brilliant Labs开发的开源AI眼镜，内置多模态AI，支持视觉搜索、实时翻译和AR显示。',
                'website': 'https://brilliant.xyz',
                'logo_url': 'https://brilliant.xyz/favicon.ico',
                'categories': ['hardware', 'image'],
                'price': '$349',
                'release_year': 2024,
                'rating': 4.0,
                'trending_score': 80,
            },
            {
                'name': 'Tesla Dojo D1',
                'description': 'Tesla自研的AI训练芯片，专为自动驾驶神经网络训练优化，采用7nm工艺，算力达到362 TFLOPS。',
                'website': 'https://www.tesla.com/AI',
                'logo_url': 'https://www.tesla.com/themes/custom/tesla_frontend/assets/favicons/favicon-196x196.png',
                'categories': ['hardware'],
                'price': 'Enterprise',
                'release_year': 2023,
                'rating': 4.6,
                'trending_score': 89,
            },
            {
                'name': 'Nvidia Jetson Orin',
                'description': '边缘AI计算平台，提供高达275 TOPS算力，支持多摄像头并发处理，适用于机器人、自动驾驶等场景。',
                'website': 'https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/',
                'logo_url': 'https://www.nvidia.com/content/dam/en-zz/Solutions/about-nvidia/logo-and-brand/01-nvidia-logo-horiz-500x200-2c50-d@2x.png',
                'categories': ['hardware'],
                'price': '$599+',
                'release_year': 2023,
                'rating': 4.7,
                'trending_score': 84,
            },
            {
                'name': 'Google Coral',
                'description': '边缘AI硬件平台，提供USB加速器和开发板，支持TensorFlow Lite模型，适合物联网AI应用。',
                'website': 'https://coral.ai',
                'logo_url': 'https://www.google.com/favicon.ico',
                'categories': ['hardware'],
                'price': '$59.99',
                'release_year': 2023,
                'rating': 4.4,
                'trending_score': 75,
            },
            {
                'name': 'Intel Gaudi3',
                'description': 'Intel最新AI加速器，专为训练和推理大语言模型设计，提供高性价比的AI算力解决方案。',
                'website': 'https://www.intel.com/content/www/us/en/products/details/processors/ai-accelerators/gaudi.html',
                'logo_url': 'https://www.intel.com/content/dam/www/central-libraries/us/en/images/intel-favicon.png',
                'categories': ['hardware'],
                'price': '$10,000+',
                'release_year': 2024,
                'rating': 4.5,
                'trending_score': 83,
            },
            {
                'name': 'SambaNova SN40L',
                'description': '专为企业AI设计的DataScale系统，提供极致性能和能效比，支持大规模模型训练和推理。',
                'website': 'https://sambanova.ai/products/datascale',
                'logo_url': 'https://sambanova.ai/favicon.ico',
                'categories': ['hardware'],
                'price': 'Enterprise',
                'release_year': 2024,
                'rating': 4.6,
                'trending_score': 81,
            },
            {
                'name': 'Groq LPU',
                'description': '语言处理单元(LPU)，专为LLM推理优化，提供超低延迟和极高吞吐量，速度远超传统GPU。',
                'website': 'https://groq.com',
                'logo_url': 'https://groq.com/favicon.ico',
                'categories': ['hardware'],
                'price': 'Cloud Service',
                'release_year': 2024,
                'rating': 4.7,
                'trending_score': 88,
            },
            {
                'name': 'Amazon Trainium2',
                'description': 'AWS第二代AI训练芯片，性能提升4倍，专为大规模模型训练优化，降低训练成本。',
                'website': 'https://aws.amazon.com/machine-learning/trainium/',
                'logo_url': 'https://a0.awsstatic.com/libra-css/images/logos/aws_logo_smile_1200x630.png',
                'categories': ['hardware'],
                'price': 'Cloud Service',
                'release_year': 2024,
                'rating': 4.5,
                'trending_score': 82,
            },
            {
                'name': 'Raspberry Pi AI Kit',
                'description': 'Raspberry Pi官方AI扩展套件，搭载Hailo-8 AI加速器，为树莓派带来13 TOPS算力。',
                'website': 'https://www.raspberrypi.com/products/ai-kit/',
                'logo_url': 'https://www.raspberrypi.com/app/uploads/2022/02/COLOUR-Raspberry-Pi-Symbol-Registered.png',
                'categories': ['hardware'],
                'price': '$70',
                'release_year': 2024,
                'rating': 4.4,
                'trending_score': 79,
            },
            # ========== 2025-2026 NEW RELEASES ==========
            # NVIDIA Rubin Platform (CES 2026)
            {
                'name': 'NVIDIA Rubin GPU',
                'description': 'NVIDIA下一代AI GPU，采用Rubin架构，相比Blackwell推理成本降低10倍，训练MoE模型所需GPU减少4倍。2026年下半年上市。',
                'website': 'https://www.nvidia.com/en-us/data-center/',
                'logo_url': 'https://www.nvidia.com/content/dam/en-zz/Solutions/about-nvidia/logo-and-brand/01-nvidia-logo-horiz-500x200-2c50-d@2x.png',
                'categories': ['hardware'],
                'price': 'Enterprise',
                'release_year': 2026,
                'rating': 5.0,
                'trending_score': 100,
            },
            {
                'name': 'NVIDIA Vera CPU',
                'description': 'NVIDIA首款ARM架构CPU，专为Rubin平台设计，与Rubin GPU协同工作，构建下一代AI超级计算机。',
                'website': 'https://www.nvidia.com/en-us/data-center/',
                'logo_url': 'https://www.nvidia.com/content/dam/en-zz/Solutions/about-nvidia/logo-and-brand/01-nvidia-logo-horiz-500x200-2c50-d@2x.png',
                'categories': ['hardware'],
                'price': 'Enterprise',
                'release_year': 2026,
                'rating': 4.9,
                'trending_score': 98,
            },
            {
                'name': 'NVIDIA Vera Rubin Superchip',
                'description': '集成1个Vera CPU和2个Rubin GPU的超级芯片，单芯片即可提供强大的AI训练和推理能力。',
                'website': 'https://www.nvidia.com/en-us/data-center/',
                'logo_url': 'https://www.nvidia.com/content/dam/en-zz/Solutions/about-nvidia/logo-and-brand/01-nvidia-logo-horiz-500x200-2c50-d@2x.png',
                'categories': ['hardware'],
                'price': 'Enterprise',
                'release_year': 2026,
                'rating': 4.9,
                'trending_score': 99,
            },
            # AMD CES 2026 Announcements
            {
                'name': 'AMD MI455X',
                'description': 'AMD Helios平台旗舰AI加速器，配备72颗MI455X芯片，直接对标NVIDIA NVL72，号称全球最强AI机架。',
                'website': 'https://www.amd.com/en/products/accelerators/instinct.html',
                'logo_url': 'https://www.amd.com/etc.clientlibs/settings/wcm/designs/amd/images/favicons/favicon-32.png',
                'categories': ['hardware'],
                'price': 'Enterprise',
                'release_year': 2026,
                'rating': 4.8,
                'trending_score': 96,
            },
            {
                'name': 'AMD MI500 Series',
                'description': 'AMD下一代数据中心GPU，相比MI300X性能提升高达1000倍，采用全新架构设计。',
                'website': 'https://www.amd.com/en/products/accelerators/instinct.html',
                'logo_url': 'https://www.amd.com/etc.clientlibs/settings/wcm/designs/amd/images/favicons/favicon-32.png',
                'categories': ['hardware'],
                'price': 'Enterprise',
                'release_year': 2026,
                'rating': 4.8,
                'trending_score': 95,
            },
            {
                'name': 'AMD Ryzen AI Max+ 392',
                'description': 'AMD最强AI PC处理器，支持本地运行2000亿参数模型，128GB统一内存，桌面级AI性能装进笔记本。',
                'website': 'https://www.amd.com/en/products/processors/laptop/ryzen/ai-max-series.html',
                'logo_url': 'https://www.amd.com/etc.clientlibs/settings/wcm/designs/amd/images/favicons/favicon-32.png',
                'categories': ['hardware'],
                'price': '$2,500+',
                'release_year': 2026,
                'rating': 4.7,
                'trending_score': 94,
            },
            {
                'name': 'AMD Ryzen AI Halo',
                'description': 'AMD AI开发者专用迷你主机，搭载Ryzen AI Max+处理器，最高128GB内存，可本地运行大模型开发。',
                'website': 'https://www.amd.com/en/products/processors/laptop/ryzen/ai-max-series.html',
                'logo_url': 'https://www.amd.com/etc.clientlibs/settings/wcm/designs/amd/images/favicons/favicon-32.png',
                'categories': ['hardware'],
                'price': '$3,000+',
                'release_year': 2026,
                'rating': 4.6,
                'trending_score': 90,
            },
            # Intel CES 2026
            {
                'name': 'Intel Panther Lake',
                'description': 'Intel Core Ultra 300系列处理器，采用Xe3图形架构，升级NPU，回归效率核心设计。',
                'website': 'https://www.intel.com/content/www/us/en/products/details/processors/core-ultra.html',
                'logo_url': 'https://www.intel.com/content/dam/www/central-libraries/us/en/images/intel-favicon.png',
                'categories': ['hardware'],
                'price': '$500+',
                'release_year': 2026,
                'rating': 4.5,
                'trending_score': 88,
            },
            {
                'name': 'Intel ARC B770',
                'description': 'Intel ARC系列高端显卡，配备32个Xe2核心，16GB显存，面向主流游戏和AI创作市场。',
                'website': 'https://www.intel.com/content/www/us/en/products/details/discrete-gpus/arc.html',
                'logo_url': 'https://www.intel.com/content/dam/www/central-libraries/us/en/images/intel-favicon.png',
                'categories': ['hardware'],
                'price': '$400+',
                'release_year': 2026,
                'rating': 4.4,
                'trending_score': 85,
            },
            # Smart Glasses 2025-2026
            {
                'name': 'Ray-Ban Meta Gen 2',
                'description': 'Meta与Ray-Ban合作的第二代AI眼镜，1200万像素摄像头，3K视频录制，升级Meta AI助手，支持慢动作视频。',
                'website': 'https://www.meta.com/smart-glasses/',
                'logo_url': 'https://static.xx.fbcdn.net/rsrc.php/yb/r/hLRJ1GG_y0J.ico',
                'categories': ['hardware', 'voice', 'image'],
                'price': '$299',
                'release_year': 2024,
                'rating': 4.6,
                'trending_score': 93,
            },
            {
                'name': 'Solos AirGo3',
                'description': 'AI智能眼镜，10小时超长续航，支持ChatGPT语音交互，健身数据追踪，需订阅AI功能。',
                'website': 'https://solosglasses.com/products/airgo-3',
                'logo_url': 'https://solosglasses.com/favicon.ico',
                'categories': ['hardware', 'voice'],
                'price': '$249',
                'release_year': 2024,
                'rating': 4.2,
                'trending_score': 82,
            },
            {
                'name': 'Even Reals G1',
                'description': '轻量级AI眼镜，实时翻译，导航显示，支持处方镜片，隐形LED微显示器，日常佩戴无违和感。',
                'website': 'https://www.evenrealities.com',
                'logo_url': 'https://www.evenrealities.com/favicon.ico',
                'categories': ['hardware', 'voice', 'image'],
                'price': '$599',
                'release_year': 2025,
                'rating': 4.3,
                'trending_score': 87,
            },
            {
                'name': 'Rokid AR Lite',
                'description': '高端AR眼镜，1200p双眼显示，色彩表现优秀，对比度高，配备高品质扬声器。',
                'website': 'https://www.rokid.com/en/product/ar-lite',
                'logo_url': 'https://www.rokid.com/favicon.ico',
                'categories': ['hardware', 'image'],
                'price': '$749',
                'release_year': 2025,
                'rating': 4.4,
                'trending_score': 84,
            },
            {
                'name': 'XREAL Air 2 Pro',
                'description': '可穿戴显示设备，Micro-OLED屏幕，等效130寸虚拟巨幕，支持电致变色调光。',
                'website': 'https://www.xreal.com/air2pro',
                'logo_url': 'https://www.xreal.com/favicon.ico',
                'categories': ['hardware', 'image'],
                'price': '$449',
                'release_year': 2024,
                'rating': 4.3,
                'trending_score': 83,
            },
            {
                'name': 'RayNeo Air 3s Pro',
                'description': '高性价比AR眼镜，明亮鲜艳的显示效果，支持多种设备连接，入门级AR体验首选。',
                'website': 'https://www.rayneo.com/products/air3s-pro',
                'logo_url': 'https://www.rayneo.com/favicon.ico',
                'categories': ['hardware', 'image'],
                'price': '$379',
                'release_year': 2025,
                'rating': 4.1,
                'trending_score': 80,
            },
            # Upcoming 2026 Smart Glasses
            {
                'name': 'Google Android XR Glasses',
                'description': 'Google重返智能眼镜市场，基于Android XR平台，搭载Gemini AI，与Warby Parker和Gentle Monster合作设计。',
                'website': 'https://www.android.com/xr/',
                'logo_url': 'https://www.google.com/favicon.ico',
                'categories': ['hardware', 'voice', 'image'],
                'price': 'TBA',
                'release_year': 2026,
                'rating': 4.7,
                'trending_score': 92,
            },
            {
                'name': 'Snap Spectacles Consumer',
                'description': 'Snap消费级AR眼镜，比开发者版更轻更小，增强现实和AI功能结合，主打社交AR体验。',
                'website': 'https://www.spectacles.com',
                'logo_url': 'https://www.spectacles.com/favicon.ico',
                'categories': ['hardware', 'image'],
                'price': 'TBA',
                'release_year': 2026,
                'rating': 4.5,
                'trending_score': 88,
            },
            {
                'name': 'Apple AI Glasses',
                'description': 'Apple放缓Vision Pro更新，转向开发AI智能眼镜，对标Meta Ray-Ban，预计2026年底发布。',
                'website': 'https://www.apple.com',
                'logo_url': 'https://www.apple.com/ac/globalnav/7/en_US/images/be15095f-5a20-57d0-ad14-cf4c638e223a/globalnav_apple_image__b5er5ngrzxqq_large.svg',
                'categories': ['hardware', 'voice', 'image'],
                'price': 'TBA',
                'release_year': 2026,
                'rating': 4.8,
                'trending_score': 95,
            },
            {
                'name': 'XREAL Project Aura',
                'description': 'XREAL新一代AR眼镜，70度视场角，搭载Android XR系统，配备外置计算单元。',
                'website': 'https://www.xreal.com',
                'logo_url': 'https://www.xreal.com/favicon.ico',
                'categories': ['hardware', 'image'],
                'price': 'TBA',
                'release_year': 2026,
                'rating': 4.4,
                'trending_score': 86,
            },
        ]
        
        products = []
        for item in hardware_products:
            product = self.create_product(
                name=item['name'],
                description=item['description'],
                logo_url=item.get('logo_url', ''),
                website=item['website'],
                categories=item['categories'],
                rating=item.get('rating', 4.5),
                weekly_users=0,  # 硬件产品用其他指标
                trending_score=item.get('trending_score', 75),
                is_hardware=True,
                source='ai_hardware',
                extra={
                    'price': item.get('price', ''),
                    'release_year': item.get('release_year', 2024),
                }
            )
            products.append(product)
        
        return products
    
    def _crawl_tech_media(self) -> List[Dict[str, Any]]:
        """爬取科技媒体的AI硬件报道（备用）"""
        products = []
        
        # 实现媒体爬取逻辑
        # 由于需要处理各种反爬和动态加载，这里提供框架
        
        return products

