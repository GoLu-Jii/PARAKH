import asyncio
import asyncpg


async def t():
    regions = [
        "aws-0-ap-south-1",
        "aws-0-us-east-1",
        "aws-0-us-west-1",
        "aws-0-eu-central-1",
        "aws-0-eu-west-1",
        "aws-0-ap-southeast-1",
        "aws-0-sa-east-1",
    ]
    for r in regions:
        url = f"postgresql://postgres.uhnampnobiroewwroipq:gauravjoshiJII%40123@{r}.pooler.supabase.com:6543/postgres"
        try:
            print("Testing region:", r)
            conn = await asyncpg.connect(url, timeout=5)
            val = await conn.fetchval("SELECT 1")
            print("FOUND REGION! SUCCESS:", r, val)
            await conn.close()
            return
        except Exception as e:
            print(f"Failed {r}:", e)


if __name__ == "__main__":
    asyncio.run(t())
