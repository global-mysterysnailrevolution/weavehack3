using StackExchange.Redis;

public class ConnectBasicExample
{

    public void run()
    {
        var muxer = ConnectionMultiplexer.Connect(
            new ConfigurationOptions{
                EndPoints= { {"redis-17120.c289.us-west-1-2.ec2.cloud.redislabs.com", 17120} },
                User="default",
                Password="<REDIS_PASSWORD>"
            }
        );
        var db = muxer.GetDatabase();

        db.StringSet("foo", "bar");
        RedisValue result = db.StringGet("foo");
        Console.WriteLine(result); // >>> bar

    }
}
