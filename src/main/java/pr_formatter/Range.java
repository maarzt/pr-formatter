package pr_formatter;

import java.util.Objects;

class Range
{

	public final int start;

	public final int end;

	public Range( int start, int end )
	{
		this.start = start;
		this.end = end;
	}

	public static Range newStartLength( int start, int length )
	{
		return new Range( start, start + length );
	}

	@Override
	public boolean equals( Object o )
	{
		if ( this == o )
			return true;
		if ( o == null || getClass() != o.getClass() )
			return false;
		Range range = ( Range ) o;
		return start == range.start && end == range.end;
	}

	@Override
	public int hashCode()
	{
		return Objects.hash( start, end );
	}
}
