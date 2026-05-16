<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
        indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv84to85">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv84to85"/>
    </xsl:copy>
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>8.4</literal> to <literal>8.5</literal>.
</para>
<xsl:template match="image" mode="conv84to85">
    <xsl:choose>
        <!-- nothing to do if already at 8.5 -->
        <xsl:when test="@schemaversion > 8.4">
            <xsl:copy-of select="."/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="8.5">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates  mode="conv84to85"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- toplevel processing instructions and comments -->
<xsl:template match="processing-instruction()|comment()" mode="conv84to85">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv84to85"/>
    </xsl:copy>
</xsl:template>

<!-- delete vga attribute from type -->
<para xmlns="http://docbook.org/ns/docbook">
    Delete obsolete vga attribute from type
</para>
<xsl:template match="type" mode="conv84to85">
    <type>
        <xsl:copy-of select="@*[not(local-name(.) = 'vga')]"/>
        <xsl:apply-templates mode="conv84to85"/>
    </type>
</xsl:template>

</xsl:stylesheet>
