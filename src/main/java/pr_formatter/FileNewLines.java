package pr_formatter;

import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;

class FileNewLines
{

	public final Path file;

	public final List<Range> changes;

	FileNewLines( Path file, List<Range> changes )
	{
		this.file = file;
		this.changes = changes;
	}

	public FileNewLines( Path file, Range... changes )
	{
		this( file, Arrays.asList(changes) );
	}

	@Override
	public boolean equals( Object o )
	{
		if ( this == o )
			return true;
		if ( o == null || getClass() != o.getClass() )
			return false;
		FileNewLines that = ( FileNewLines ) o;
		return Objects.equals( file, that.file ) && Objects.equals( changes, that.changes );
	}

	@Override
	public int hashCode()
	{
		return Objects.hash( file, changes );
	}
}
