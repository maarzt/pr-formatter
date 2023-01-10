package pr_formatter;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.Charset;
import java.nio.file.Path;
import java.util.List;

import org.apache.commons.io.IOUtils;

public class RunCommand
{
	static List<String> runAndGetOutput( Path repository, String... command )
	{
		try
		{
			Process process = new ProcessBuilder( command ).directory( repository.toFile() ).start();
			process.waitFor();
			InputStream inputStream = process.getInputStream();
			return IOUtils.readLines( inputStream, Charset.defaultCharset() );
		}
		catch ( IOException | InterruptedException e )
		{
			throw new RuntimeException( e );
		}
	}
}
