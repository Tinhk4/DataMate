from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_nvidia_ai_endpoints import ChatNVIDIA

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")


# Khởi tạo rate limiter
rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.3,  # Cho phép 1 yêu cầu mỗi 3 giây (0.3 yêu cầu mỗi giây)
    check_every_n_seconds=0.1,  # Kiểm tra mỗi 100 ms
    max_bucket_size=10  # Kích thước tối đa của bucket
)


def load_llms_model(model_name: str):
    """
    Load the Large Language Model for DataMate
    """
    if "gpt" in model_name:
        return ChatOpenAI(
            model_name=model_name,
            temperature=0.1,
            max_tokens=1000,
        )
    elif "gemini" in model_name:
        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.1,
            max_tokens=None,
            timeout=None,
            max_retries=1,
            rate_limiter=rate_limiter,
            debug=True,
            # other params...
        )
    elif "llama" in model_name:
        print("Loading LLAMA model...")
        # return ChatPerplexity(
        #     model="llama-3.1-sonar-large-128k-online",
        #     temperature=0.1,
        #     max_tokens=1024,
        # )

        return ChatNVIDIA(
            model="meta/llama-3.1-405b-instruct",
            temperature=0.1,
            max_tokens=1024,
            max_retries=2,
            timeout=10,
        )

    else:
        raise ValueError("Model not supported")
