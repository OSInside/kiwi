<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
        indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv83to84">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv83to84"/>
    </xsl:copy>
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>8.3</literal> to <literal>8.4</literal>.
</para>
<xsl:template match="image" mode="conv83to84">
    <xsl:choose>
        <!-- nothing to do if already at 8.4 -->
        <xsl:when test="@schemaversion > 8.3">
            <xsl:copy-of select="."/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="8.4">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates  mode="conv83to84"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- toplevel processing instructions and comments -->
<xsl:template match="processing-instruction()|comment()" mode="conv83to84">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv83to84"/>
    </xsl:copy>
</xsl:template>

<!-- rename console attribute to output_console and input_console-->
<xsl:template match="bootloader" mode="conv83to84">
    <bootloader>
        <xsl:copy-of select="@*[not(local-name(.) = 'console')]"/>
        <xsl:if test="@console">
            <xsl:choose>
                <xsl:when test="contains(@console, ' ')">
                    <xsl:attribute name="output_console">
                        <xsl:value-of select="substring-before(@console,' ')"/>
                    </xsl:attribute>
                    <xsl:attribute name="input_console">
                        <xsl:value-of select="substring-after(@console,' ')"/>
                    </xsl:attribute>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:attribute name="output_console">
                        <xsl:value-of select="@console"/>
                    </xsl:attribute>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
        <xsl:apply-templates  mode="conv83to84"/>
    </bootloader>
</xsl:template>

</xsl:stylesheet>
